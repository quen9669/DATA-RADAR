"""Moovijob blocks scripts and datacenter IPs: read it with a real Chrome on a home PC. `python moovijob_local.py [N offers]` writes raw pages to moovijob_raw.jsonl.gz."""
import datetime, gzip, json, os, re, sys
from playwright.sync_api import sync_playwright

from radar import NOISE

PAUSE = 4  # seconds between two pages
LINK = re.compile(r"https://www\.moovijob\.com/offres-emploi/(?!jobs-luxembourg)[^/\"'\\ <>#?]+/[^/\"'\\ <>#?]+")


def read(page, url):
    page.goto(url, timeout=60000)
    page.wait_for_function("!/Just a moment|Un instant/.test(document.title)", timeout=600000)  # Cloudflare check: a person ticks it, the script waits up to 10 min, in English or French
    page.wait_for_timeout(PAUSE * 1000)  # slow on purpose: faster than this and Cloudflare keeps the check up
    return page.content()


def done(path):
    """Urls already saved, so a restart resumes where it stopped."""
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return {json.loads(line)["item_id"] for line in f}
    except (OSError, EOFError):
        return set()


def main(limit=100, path="moovijob_raw.jsonl.gz"):
    urls, n, saved = [], 1, done(path)
    with sync_playwright() as p, gzip.open(path, "at", encoding="utf-8") as out:
        page = p.chromium.launch_persistent_context("moovijob_profile", channel="chrome", headless=False).new_page()  # saved profile: tick the Cloudflare check once by hand
        while len(urls) < limit:
            found = sorted(set(LINK.findall(read(page, f"https://www.moovijob.com/offres-emploi/jobs-luxembourg?page={n}"))) - set(urls))
            if not found:
                break
            urls, n = urls + found, n + 1
        for u in sorted(set(urls[:limit]) - saved):
            try:
                out.write(json.dumps({"item_id": u, "fetched_at": datetime.datetime.now().isoformat(), "body": NOISE.sub("", read(page, u))}, ensure_ascii=False) + "\n")
                out.flush()
            except Exception as e:
                print(u, e, file=sys.stderr, flush=True)  # retried at the next run
                continue
            print(u, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
