"""Collect: one function per method, shared by every source. Raw items go to Parquet on R2, parsing is dbt's job."""
import csv, datetime, json, os, re, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

from salary import parse

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


def api(src, page, url=None):
    body = json.loads(fill(src["body"], page)) if src["body"] else None
    return http(fill(src["url"], page), body)


def page(src, page, url=None):
    return http(url or fill(src["url"], page))


def firecrawl(src, page, url=None):
    key = {"Authorization": "Bearer " + os.environ["FIRECRAWL_API_KEY"]}
    return http("https://api.firecrawl.dev/v1/scrape", {"url": url or fill(src["fallback_url"] or src["url"], page), "formats": ["rawHtml"], "waitFor": 8000}, key)


def jobspy(src, page, url=None):
    """JobSpy scrape of every search term of the source, de-duplicated: one JSON list. src["body"]["jobspy"] holds its arguments."""
    from jobspy import scrape_jobs
    args = json.loads(src["body"])["jobspy"]
    jobs = {}
    for term in args.pop("search_terms"):
        jobs |= {j["id"]: j for j in json.loads(scrape_jobs(search_term=term, **args).to_json(orient="records", date_format="iso"))}
    return json.dumps(list(jobs.values()), ensure_ascii=False)


def apify(src, page, url=None):
    """Run an Apify actor and return its dataset (a JSON list). src["fallback_url"] is the actor endpoint, src["body"]["apify"] its input."""
    return http(src["fallback_url"], json.loads(src["body"])["apify"], {"Authorization": "Bearer " + os.environ["APIFY_TOKEN"]})


METHODS = {"api": api, "page": page, "firecrawl": firecrawl, "jobspy": jobspy, "apify": apify}
LISTS = ("api", "jobspy", "apify")  # methods whose answer is a list of items


def split(src, method, text, page=0):
    """(items, envelope): list methods hold many items, any other method keeps the page whole."""
    if method not in LISTS:
        return [(fill(src["url"] if method == "page" else src["fallback_url"] or src["url"], page), text)] * bool(text.strip()), None
    doc = json.loads(text)
    items = at(doc, src["items"])
    envelope = text if isinstance(doc, list) else json.dumps({**doc, src["items"]: []})
    return [(str(at(i, src["id"])), json.dumps(i, ensure_ascii=False)) for i in items], envelope


def links(src, method, text):
    """Detail page links of a listing page (src["follow"] is a regex matching the href), made absolute."""
    if not src.get("follow") or method in LISTS:
        return set()
    return {urljoin(fill(src.get("url", ""), 0), u) for u in re.findall(src["follow"], text)}


def follow(src, method, rows, cap=None):
    """Detail pages linked from the listings, only those not stored yet; one that fails is retried at the next run."""
    urls = sorted(set().union(*(links(src, method, r[4]) for r in rows)) - known(src["source"]))[:cap]

    def get(u):
        try:
            return (src["source"], method, 0, u, METHODS[method](src, 0, u), None)
        except Exception as e:
            print(u, e, file=sys.stderr)

    with ThreadPoolExecutor(8) as pool:
        return [r for r in pool.map(get, urls) if r]


def known(source):
    try:
        return {r[0] for r in connect().execute(f"SELECT DISTINCT item_id FROM read_parquet('r2://{BUCKET}/raw/source={source}/*/*.parquet')").fetchall()}
    except Exception:
        return set()


def pull(src, method, pages, cap=None):
    """Listing pages until a short page (lists) or a page with no new detail link (pages); then the new detail pages."""
    rows, first, seen = [], int(src["first"]), set()
    for page in range(first, first + pages):
        items, envelope = split(src, method, METHODS[method](src, page), page)
        print(src["source"], method, page, len(items), flush=True)
        rows += [(src["source"], method, page, i, body, envelope if n == 0 else None) for n, (i, body) in enumerate(items)]
        new = set().union(*(links(src, method, b) for _, b in items)) - seen
        seen |= new
        if (len(items) < int(src["size"])) if method in LISTS else not new:
            break
    return rows + follow(src, method, rows, cap)


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
    key, secret, account = (os.environ[k] for k in ("R2_KEY_ID", "R2_SECRET", "R2_ACCOUNT_ID"))
    con.execute(f"CREATE SECRET (TYPE r2, KEY_ID '{key}', SECRET '{secret}', ACCOUNT_ID '{account}')")
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
                rows = pull(src, method, 1, cap=5)
                pct = sum(bool((p := parse(r[4])) and not p["excluded"]) for r in rows) * 100 // max(len(rows), 1)
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
    if failed:
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
