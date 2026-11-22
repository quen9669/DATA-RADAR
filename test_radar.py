import json, unittest
from unittest import mock

import radar

JOB_ROOM = {"source": "job_room", "items": "", "id": "jobAdvertisement.id", "size": "2", "first": "0", "methods": "api firecrawl", "fallback_url": "u"}
EURES = {**JOB_ROOM, "source": "eures", "items": "jvs", "id": "id"}


class SplitTest(unittest.TestCase):
    def test_list_response_one_row_per_item(self):
        text = json.dumps([{"jobAdvertisement": {"id": "a"}}, {"jobAdvertisement": {"id": "b"}}])
        items, envelope = radar.split(JOB_ROOM, "api", text)
        self.assertEqual([i for i, _ in items], ["a", "b"])
        self.assertEqual(envelope, text)

    def test_envelope_keeps_everything_but_the_items(self):
        items, envelope = radar.split(EURES, "api", json.dumps({"numberRecords": 9, "jvs": [{"id": "x", "title": "t"}]}))
        self.assertEqual(json.loads(envelope), {"numberRecords": 9, "jvs": []})
        self.assertEqual(json.loads(items[0][1])["title"], "t")

    def test_other_methods_keep_the_page_whole(self):
        self.assertEqual(radar.split(JOB_ROOM, "firecrawl", "<html>"), ([("u", "<html>")], None))


class PullTest(unittest.TestCase):
    def pages(self, *counts):
        return [json.dumps([{"jobAdvertisement": {"id": f"{p}-{n}"}} for n in range(c)]) for p, c in enumerate(counts)]

    def test_stops_on_a_short_page(self):
        with mock.patch.dict(radar.METHODS, {"api": lambda src, page: self.pages(2, 1, 2)[page]}):
            self.assertEqual(len(radar.pull(JOB_ROOM, "api", 10)), 3)

    def test_stops_at_the_page_limit(self):
        with mock.patch.dict(radar.METHODS, {"api": lambda src, page: self.pages(2, 2, 2)[page]}):
            self.assertEqual(len(radar.pull(JOB_ROOM, "api", 2)), 4)

    def test_falls_back_when_the_main_method_fails(self):
        def broken(src, page):
            raise OSError("blocked")
        with mock.patch.dict(radar.METHODS, {"api": broken, "firecrawl": lambda src, page: "<html>"}):
            self.assertEqual(radar.collect(JOB_ROOM, 1)[0][1], "firecrawl")

    def test_fails_loudly_when_every_method_fails(self):
        with mock.patch.dict(radar.METHODS, {"api": lambda src, page: "[]", "firecrawl": lambda src, page: ""}):
            with self.assertRaisesRegex(RuntimeError, "job_room failed"):
                radar.collect(JOB_ROOM, 1)

    def test_follows_only_new_detail_links(self):
        listing = '{"rawHtml": "<a href=\\"https://x.lu/offre/a-1.html\\"> <a href=\\"https://x.lu/offre/b-2.html\\">"}'
        src = {**JOB_ROOM, "follow": r"https://x\.lu/offre/[^\"\\\\ <>]+\.html"}
        with mock.patch.object(radar, "known", return_value={"https://x.lu/offre/a-1.html"}), \
                mock.patch.dict(radar.METHODS, {"firecrawl": lambda s, page, url=None: f"page of {url}"}):
            rows = radar.follow(src, "firecrawl", [("s", "firecrawl", 1, "u", listing, None)])
        self.assertEqual([(r[3], r[4]) for r in rows], [("https://x.lu/offre/b-2.html", "page of https://x.lu/offre/b-2.html")])


class PageTest(unittest.TestCase):
    SRC = {**JOB_ROOM, "source": "site", "url": "https://x.lu/jobs?page={page}", "fallback_url": "", "follow": r"(?:https://x\.lu)?/offre/[^\"' <>]+", "first": "1"}

    def run_pull(self, listings, cap=None):
        fetched = []

        def fetch(src, page, url=None):
            fetched.append(url or page)
            return listings[page - 1] if url is None else f"detail {url}"
        with mock.patch.object(radar, "known", return_value=set()), mock.patch.dict(radar.METHODS, {"page": fetch}):
            return radar.pull(self.SRC, "page", 5, cap), fetched

    def test_page_code_is_dropped_but_the_offer_data_is_kept(self):
        html = '<svg><path d="M0"/></svg><style>a{}</style><script>track()</script><script type="application/ld+json">{"@type":"JobPosting"}</script><p>Offre</p>'
        (_, kept), = radar.split(self.SRC, "page", html)[0]
        self.assertEqual(kept, '<script type="application/ld+json">{"@type":"JobPosting"}</script><p>Offre</p>')

    def test_pages_stop_when_no_new_link_and_relative_links_are_made_absolute(self):
        rows, _ = self.run_pull(['<a href="/offre/a"> <a href="/offre/b">', '<a href="/offre/b">', '<a href="/offre/c">'])
        self.assertEqual([r[3] for r in rows], ["https://x.lu/jobs?page=1", "https://x.lu/jobs?page=2", "https://x.lu/offre/a", "https://x.lu/offre/b"])

    def test_cap_limits_detail_pages(self):
        rows, _ = self.run_pull(['<a href="/offre/a"> <a href="/offre/b">', ""], cap=1)
        self.assertEqual(len(rows), 2)

    def test_a_failing_detail_page_is_skipped(self):
        def fetch(src, page, url=None):
            if url == "https://x.lu/offre/a":
                raise OSError("boom")
            return '<a href="/offre/a"> <a href="/offre/b">' if url is None else "ok"
        with mock.patch.object(radar, "known", return_value=set()), mock.patch.dict(radar.METHODS, {"page": fetch}):
            self.assertEqual([r[3] for r in radar.pull(self.SRC, "page", 1)][-1], "https://x.lu/offre/b")

    def test_a_page_failing_after_the_first_keeps_the_pages_read(self):
        def fetch(src, page, url=None):
            if url is None and page == 2:
                raise OSError("404")
            return '<a href="/offre/a">' if url is None else "ok"
        with mock.patch.object(radar, "known", return_value=set()), mock.patch.dict(radar.METHODS, {"page": fetch}):
            self.assertEqual(len(radar.pull(self.SRC, "page", 5)), 2)


if __name__ == "__main__":
    unittest.main()
