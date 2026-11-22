import collections, json, re, sys
sys.path.insert(0, ".")
import radar
src = {"url": "", "fallback_url": ""}
for url in sys.argv[1:]:
    for method in ("page", "firecrawl"):
        try:
            t = radar.METHODS[method](src, 0, url)
            if method == "firecrawl":
                t = json.loads(t)["data"]["rawHtml"]
        except Exception as e:
            print(f"## {method} {url}: {e}")
            continue
        hrefs = re.findall(r'href=["\']([^"\']+)', t)
        shapes = collections.Counter(re.sub(r"[0-9a-f]{24}", "HEX", re.sub(r"\d+", "N", h)) for h in hrefs if not re.search(r"\.(css|js|png|jpg|svg|ico|woff2?)", h))
        print(f"## {method} {url}: {len(t)} bytes, ldjson={t.count('ld+json')}, JobPosting={t.count('JobPosting')}, NEXT={t.count('__NEXT_DATA__')}, hrefs={len(hrefs)}")
        print("SHAPES", shapes.most_common(15))
        print("PAGINATION", sorted({h for h in hrefs if re.search(r"(?i)page=|/page/|[?&]p=", h)})[:5])
        print("TITLE", re.findall(r"<title>(.*?)</title>", t, re.S)[:1], "H1", re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S)[:1])
