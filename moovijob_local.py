"""Moovijob blocks scripts and datacenter IPs: read it with a real Chrome on a home PC. `python moovijob_local.py [N offers]` writes raw pages to moovijob_raw.jsonl.gz."""
import datetime, gzip, json, re, sys
from playwright.sync_api import sync_playwright

from radar import NOISE

LINK = re.compile(r"https://www\.moovijob\.com/offres-emploi/(?!jobs-luxembourg)[^/\"'\\ <>#?]+/[^/\"'\\ <>#?]+")


def read(page, url):
    page.goto(url, timeout=60000)
    page.wait_for_function("!document.title.includes('Just a moment')", timeout=60000)
    return page.content()


def main(limit=100):
    urls, n = [], 1
    with sync_playwright() as p, gzip.open("moovijob_raw.jsonl.gz", "at", encoding="utf-8") as out:
        page = p.chromium.launch(channel="chrome", headless=False).new_page()
        while len(urls) < limit:
            found = sorted(set(LINK.findall(read(page, f"https://www.moovijob.com/offres-emploi/jobs-luxembourg?page={n}"))) - set(urls))
            if not found:
                break
            urls, n = urls + found, n + 1
        for u in urls[:limit]:
            out.write(json.dumps({"item_id": u, "fetched_at": datetime.datetime.now().isoformat(), "body": NOISE.sub("", read(page, u))}, ensure_ascii=False) + "\n")
            out.flush()
            print(u, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
