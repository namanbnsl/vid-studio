import contextlib
import io
import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vid-studio" / "scripts"))
import studio  # noqa: E402

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>
<item><title>Rate cut announced by central bank today</title><link>https://example.com/a?utm_source=x</link>
<pubDate>Sat, 10 Oct 2026 10:00:00 GMT</pubDate><description>&lt;b&gt;Big&lt;/b&gt; news</description></item>
<item><title>Second story about something else entirely</title><link>https://example.com/b</link></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>A</title>
<entry><title>Rate cut announced by central bank today - Other Paper</title>
<link rel="alternate" href="https://other.org/x"/><updated>2026-10-10</updated></entry></feed>"""

PAGE = """<html><head><title>Fallback</title><meta property="og:title" content="Real Title">
<meta property="article:published_time" content="2026-10-01"><meta property="og:site_name" content="Example News">
<script>var x=1;</script></head><body><nav>Menu</nav><h1>Heading</h1><p>""" + "Body text. " * 80 + "</p></body></html>"


class StudioTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ws = self.root / "ws"
        self.run_cli("init")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            studio.main(["--workspace", str(self.ws), *args])
        return output.getvalue()

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path.as_uri()

    def test_status_on_fresh_workspace_points_to_setup(self):
        output = self.run_cli("status")
        self.assertIn("Setup: incomplete", output)
        self.assertIn("references/setup.md", output)

    def test_workspace_flag_after_subcommand(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            studio.main(["status", "--workspace", str(self.ws)])
        self.assertIn(str(self.ws), output.getvalue())

    def test_scan_dedupes_by_url_and_title_across_feeds(self):
        self.run_cli("add-source", "--name", "RSS", "--feed", self.write("a.xml", RSS))
        self.run_cli("add-source", "--name", "Atom", "--feed", self.write("b.xml", ATOM))
        first = self.run_cli("scan")
        self.assertIn("New items: 2", first)
        inbox = (self.ws / "inbox" / f"{studio.today()}.md").read_text()
        self.assertIn("Rate cut announced", inbox)
        self.assertIn("Big news", inbox)
        self.assertNotIn("other.org", inbox)  # same headline, different feed
        self.assertIn("New items: 0", self.run_cli("scan"))
        self.assertIn("2 items since last triage", self.run_cli("status"))
        self.run_cli("triaged")
        self.assertIn("0 items since last triage", self.run_cli("status"))

    def test_add_source_discovers_feed_from_page(self):
        feed_uri = self.write("feed.xml", RSS)
        page = self.write("site.html", f'<html><head><link rel="alternate" type="application/rss+xml" href="{feed_uri}"></head></html>')
        output = self.run_cli("add-source", "--name", "Site", "--url", page)
        self.assertIn("feed found", output)
        source = json.loads((self.ws / "sources.json").read_text())["sources"][0]
        self.assertEqual(source["feed"], feed_uri)

    def test_page_without_feed_is_listed_for_manual_check(self):
        self.run_cli("add-source", "--name", "Plain", "--url", self.write("plain.html", "<p>hi</p>"))
        self.assertIn("Check these pages yourself", self.run_cli("scan"))

    def test_news_query_uses_locale(self):
        studio_json = json.loads((self.ws / "studio.json").read_text())
        studio_json["locale"] = {"language": "hi", "country": "IN"}
        (self.ws / "studio.json").write_text(json.dumps(studio_json))
        with unittest.mock.patch.object(studio, "try_feed", return_value=True):
            self.run_cli("add-source", "--news-query", "UPI fraud")
        source = json.loads((self.ws / "sources.json").read_text())["sources"][0]
        self.assertIn("q=UPI+fraud&hl=hi-IN&gl=IN&ceid=IN:hi", source["feed"])

    def test_trends_feed_uses_news_item_url(self):
        trends = """<rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0"><channel>
        <item><title>cricket</title><ht:approx_traffic>500+</ht:approx_traffic>
        <link>https://trends.google.com/trending/rss?geo=IN</link>
        <ht:news_item><ht:news_item_url>https://news.example/story</ht:news_item_url></ht:news_item></item></channel></rss>"""
        items = studio.parse_feed(trends.encode())
        self.assertEqual(items[0]["url"], "https://news.example/story")
        self.assertIn("500+", items[0]["summary"])

    def test_daily_topic_project_lifecycle(self):
        self.run_cli("add-topic", "--title", "UPI growth", "--mode", "daily", "--status", "active")
        self.assertIn("daily due: upi-growth", self.run_cli("status"))
        self.run_cli("lead", "--topic", "upi-growth", "--url", "https://x.org/1", "--title", "Lead")
        self.run_cli("new-project", "--topic", "upi-growth")
        project_id = f"{studio.today()}-upi-growth"
        project = json.loads((self.ws / "projects" / project_id / "project.json").read_text())
        self.assertEqual(project["leads"][0]["url"], "https://x.org/1")
        self.assertIn("UPI growth", (self.ws / "projects" / project_id / "plan.md").read_text())
        topic = json.loads((self.ws / "topics.json").read_text())["topics"][0]
        self.assertEqual(topic["leads"], [])
        self.assertEqual(topic["last_run"], studio.today())
        self.assertNotIn("daily due", self.run_cli("status"))

        # Second project for the same topic links the first as its baseline.
        output = self.run_cli("new-project", "--topic", "upi-growth")
        self.assertIn(project_id, output)

    def test_no_news_marks_topic_run(self):
        self.run_cli("add-topic", "--title", "Chips", "--mode", "daily", "--status", "active")
        self.run_cli("no-news", "--topic", "chips", "--note", "nothing since yesterday")
        topic = json.loads((self.ws / "topics.json").read_text())["topics"][0]
        self.assertEqual(topic["history"][-1]["result"], "no-news")

    def test_snapshot_check_and_stage_gate(self):
        self.run_cli("new-project", "--title", "Test")
        project_id = f"{studio.today()}-test"
        project = self.ws / "projects" / project_id
        output = self.run_cli("snapshot", project_id, self.write("page.html", PAGE))
        self.assertIn("S1: Real Title · Example News", output)
        evidence = (project / "evidence" / "S1.md").read_text()
        self.assertIn("published: 2026-10-01", evidence)
        self.assertIn("## Heading", evidence)
        self.assertNotIn("Menu", evidence)
        self.assertNotIn("var x", evidence)
        self.assertIn("Already captured", self.run_cli("snapshot", project_id, self.write("page.html", PAGE)))

        text_file = self.root / "manual.txt"
        text_file.write_text("Official statistic: 42 widgets.")
        self.run_cli("snapshot", project_id, "https://stats.gov/table", "--type", "data", "--title", "Table", "--text-file", str(text_file))

        claims = {"claims": [
            {"id": "C1", "text": "42 widgets", "sources": ["S2"], "status": "verified"},
            {"id": "C2", "text": "Body text", "sources": ["S1"], "status": "verified"},
            {"id": "C3", "text": "Rumour", "sources": [], "status": "unverified"},
        ]}
        (project / "claims.json").write_text(json.dumps(claims))
        (project / "script.md").write_text("Fact [C1]. Other [C2, C3]. Ghost [C9].")
        (project / "brief.md").write_text("ok [C1]")
        (project / "post.md").write_text("ok")
        with self.assertRaises(SystemExit):
            self.run_cli("check", project_id)
        with self.assertRaises(SystemExit):
            self.run_cli("stage", project_id, "script-review")

        errors, _, _ = studio.run_checks(project)
        joined = "\n".join(errors)
        self.assertIn("C2: 'verified' needs", joined)  # one secondary source
        self.assertIn("unverified claim C3", joined)
        self.assertIn("unknown claim C9", joined)
        self.assertNotIn("C1:", joined)  # data source is strong enough alone

        claims["claims"][1]["status"] = "single-source"
        (project / "claims.json").write_text(json.dumps(claims))
        (project / "script.md").write_text("Fact [C1]. Other [C2].")
        self.assertIn("Check passed", self.run_cli("check", project_id))
        self.run_cli("stage", project_id, "script-review")
        self.assertEqual(json.loads((project / "project.json").read_text())["stage"], "script-review")


if __name__ == "__main__":
    unittest.main()
