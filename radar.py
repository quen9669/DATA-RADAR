"""Collect: one function per method, shared by every source. Raw items go to Parquet on R2, parsing is dbt's job."""
import csv, datetime, json, os, subprocess, sys, urllib.request

BUCKET = os.environ.get("R2_BUCKET", "jobradar-data")
CAP_GB = 9.5


def http(url, body=None, headers=None):
    head = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", **(headers or {})}
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, data, head), timeout=60) as r:
        return r.read().decode()


def at(doc, path):
    for key in filter(None, path.split(".")):
        doc = doc[key]
    return doc


def fill(text, page):
    return text.replace("{page}", str(page))


def api(src, page):
    body = json.loads(fill(src["body"], page)) if src["body"] else None
    return http(fill(src["url"], page), body)


def firecrawl(src, page):
    key = {"Authorization": "Bearer " + os.environ["FIRECRAWL_API_KEY"]}
    return http("https://api.firecrawl.dev/v1/scrape", {"url": fill(src["fallback_url"], page), "formats": ["rawHtml"]}, key)


METHODS = {"api": api, "firecrawl": firecrawl}


def split(src, method, text):
    """(items, envelope): api pages hold a list of items, any other method keeps the page whole."""
    if method != "api":
        return [(src["fallback_url"], text)] * bool(text.strip()), None
    doc = json.loads(text)
    items = at(doc, src["items"])
    envelope = text if isinstance(doc, list) else json.dumps({**doc, src["items"]: []})
    return [(str(at(i, src["id"])), json.dumps(i, ensure_ascii=False)) for i in items], envelope


def pull(src, method, pages):
    rows, first = [], int(src["first"])
    for page in range(first, first + pages):
        items, envelope = split(src, method, METHODS[method](src, page))
        rows += [(src["source"], method, page, i, body, envelope if n == 0 else None) for n, (i, body) in enumerate(items)]
        if len(items) < int(src["size"]) or method != "api":
            break
    return rows


def collect(src, pages):
    errors = []
    for method in src["methods"].split():
        try:
            rows = pull(src, method, pages)
            if rows:
                return rows
            errors.append(f"{method}: no items")
        except Exception as e:
            errors.append(f"{method}: {e}")
    raise RuntimeError(f"{src['source']} failed: " + "; ".join(errors))


def connect():
    import duckdb
    con = duckdb.connect()
    con.execute("CREATE SECRET (TYPE r2, KEY_ID getenv('R2_KEY_ID'), SECRET getenv('R2_SECRET'), ACCOUNT_ID getenv('R2_ACCOUNT_ID'))")
    return con


def bucket_gb():
    out = subprocess.run(["aws", "s3", "ls", f"s3://{BUCKET}", "--recursive", "--summarize", "--endpoint-url", r2_endpoint()],
                         capture_output=True, text=True, check=True).stdout
    return int(out.split("Total Size:")[1]) / 1e9


def r2_endpoint():
    return f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"


def save(src, rows):
    day = datetime.date.today().isoformat()
    con = connect()
    con.execute("CREATE TABLE t (source VARCHAR, method VARCHAR, page INT, item_id VARCHAR, body VARCHAR, envelope VARCHAR)")
    con.executemany("INSERT INTO t VALUES (?, ?, ?, ?, ?, ?)", rows)
    path = f"r2://{BUCKET}/raw/source={src['source']}/date={day}/{datetime.datetime.now():%H%M%S}.parquet"
    con.execute(f"COPY (SELECT *, now() AS fetched_at FROM t) TO '{path}' (FORMAT parquet, COMPRESSION zstd)")
    return len(rows)


def sources(only=None):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.csv"), newline="") as f:
        return [r for r in csv.DictReader(f) if only in (None, r["source"])]


def check():
    """Try every method of every source on one page, write nothing. Exit 1 if a source has no working method."""
    print("| source | method | result | items | with salary |\n|---|---|---|---|---|")
    bad = 0
    for src in sources():
        ok = False
        for method in src["methods"].split():
            try:
                rows = pull(src, method, 1)
                pct = sum(any(w in r[4].lower() for w in ("salar", "salaire", "gehalt", "lohn", "chf", "eur")) for r in rows) * 100 // max(len(rows), 1)
                print(f"| {src['source']} | {method} | OK | {len(rows)} | {pct}% |")
                ok = ok or bool(rows)
            except Exception as e:
                print(f"| {src['source']} | {method} | ERROR {str(e)[:80]} | 0 | |")
        bad += not ok
    sys.exit(bad > 0)


def main(arg=None):
    if arg == "check":
        return check()
    if arg == "compact":
        return compact(os.environ.get("MONTH"))
    if bucket_gb() > CAP_GB:
        sys.exit(f"bucket above {CAP_GB} GB: collection stopped")
    failed = []
    for src in sources(arg):
        try:
            print(src["source"], save(src, collect(src, int(os.environ.get("PAGES", src["max_pages"])))), "items")
        except Exception as e:
            failed.append(str(e))
            print(e, file=sys.stderr)
    sys.exit("\n".join(failed))


def compact(month):
    """One copy of each distinct version of an item, with its first and last sighting; then drop the month's raw files."""
    month = month or (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")
    con = connect()
    raw = f"r2://{BUCKET}/raw/source=*/date={month}-*/*.parquet"
    out = f"r2://{BUCKET}/compact/month={month}/data.parquet"
    con.execute(f"""COPY (SELECT source, item_id, md5(body) AS version, min(fetched_at) AS first_seen, max(fetched_at) AS last_seen,
        any_value(method) AS method, any_value(body) AS body FROM read_parquet('{raw}', hive_partitioning = true)
        GROUP BY source, item_id, md5(body)) TO '{out}' (FORMAT parquet, COMPRESSION zstd)""")
    before = con.execute(f"SELECT count(DISTINCT (source, item_id, md5(body))) FROM read_parquet('{raw}', hive_partitioning = true)").fetchone()[0]
    assert con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0] == before, "compaction lost versions"
    subprocess.run(["aws", "s3", "rm", f"s3://{BUCKET}/raw/", "--recursive", "--exclude", "*", "--include", f"source=*/date={month}-*",
                    "--endpoint-url", r2_endpoint()], check=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
