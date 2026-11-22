import json, os, re, sys
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
            print(f"## {method} {url}: {e}"); continue
        hrefs = re.findall(r'href=["\']([^"\']+)', t)
        keep = sorted({h for h in hrefs if re.search(r"(?i)job|emploi|offre|vacan|carri|sitemap|stellen", h)})
        print(f"## {method} {url}: {len(t)} bytes, title={re.findall('<title>(.*?)</title>', t, re.S)[:1]}, ldjson={t.count('ld+json')}, JobPosting={t.count('JobPosting')}, hrefs={len(hrefs)}")
        print("\n".join(keep[:40]))
