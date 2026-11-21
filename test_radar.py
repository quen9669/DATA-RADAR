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


if __name__ == "__main__":
    unittest.main()
