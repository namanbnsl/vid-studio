import contextlib
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vid-studio" / "scripts"))
import studio  # noqa: E402

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>
<item><title>Rate cut announced by central bank today</title><link>https://example.com/a?utm_source=x</link>
<pubDate>Sat, 10 Oct 2026 10:00:00 GMT</pubDate><description>&lt;b&gt;Big&lt;/b&gt; news</description></item>
</channel></rss>"""


class StudioTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "ws"
        self.cli("init")
        self.cli("new-project", "--name", "Test Project")
        self.ws = self.home / "projects" / "test-project"
        self.studio = studio.Studio(self.ws)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, stdin=None):
        output = io.StringIO()
        old_stdin = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(output):
                studio.main(["--workspace", str(self.home), *args])
        finally:
            sys.stdin = old_stdin
        return output.getvalue()

    def run_with_findings(self, findings):
        self.cli("start-run")
        run_id = self.studio.runs()[-1]["id"]
        self.cli("add-findings", "--run", run_id, "-", stdin=json.dumps(findings))
        for source_id in self.studio.runs()[-1]["sources"]:
            self.cli("checked", "--run", run_id, "--source", source_id)
        self.cli("finish-run", "--run", run_id)
        return run_id

    def test_topics_and_sources(self):
        self.cli("add-topic", "--name", "UPI & payments", "--description", "Fees and rules")
        with self.assertRaises(SystemExit):
            self.cli("add-topic", "--name", "upi & payments")  # duplicate names are rejected
        self.cli("add-source", "--url", "rbi.org.in", "--note", "Press")
        self.assertEqual(self.studio.sources()[0]["url"], "https://rbi.org.in")
        with self.assertRaises(SystemExit):
            self.cli("add-source", "--url", "https://rbi.org.in/")
        with self.assertRaises(SystemExit):
            self.cli("add-source", "--url", "javascript:alert(1)")

    def test_research_run_adds_and_merges_findings(self):
        self.cli("add-topic", "--name", "UPI")
        status = self.cli("status")
        self.assertIn("last research: never", status)
        run_id = self.run_with_findings([
            {"title": "Fee delayed", "summary": "s", "topics": ["upi"],
             "sources": [{"url": "https://a.com/1", "publisher": "A"}]},
            {"title": "Same story elsewhere", "topics": ["UPI"], "sources": ["https://b.com/2", "https://a.com/1?utm_source=x"]},
        ])
        findings = self.studio.findings()
        self.assertEqual(len(findings), 1)  # second item shares a source, so it merges
        self.assertEqual({s["url"] for s in findings[0]["sources"]}, {"https://a.com/1", "https://b.com/2"})
        run = self.studio.runs()[-1]
        self.assertEqual((run["id"], run["status"], run["findings"]), (run_id, "completed", 1))
        # The next run looks back from the last successful run, with overlap.
        since = self.studio.research_since()
        self.assertLess(since, studio.parse_time(run["started"]))

    def test_findings_are_validated(self):
        self.cli("add-topic", "--name", "UPI")
        self.cli("start-run")
        run_id = self.studio.runs()[-1]["id"]
        for bad in ([{"title": "x", "topics": ["nope"], "sources": ["https://a.com"]}],
                    [{"title": "x", "topics": ["UPI"], "sources": []}],
                    [{"title": "", "sources": ["https://a.com"]}],
                    [{"title": "x" * 200, "topics": ["UPI"], "sources": ["https://a.com"]}],
                    [{"title": "x", "summary": "y" * 400, "topics": ["UPI"], "sources": ["https://a.com"]}]):
            with self.assertRaises(SystemExit):
                self.cli("add-findings", "--run", run_id, "-", stdin=json.dumps(bad))
        self.assertEqual(self.studio.findings(), [])

    def test_stories_attach_and_detect_conflicts(self):
        self.cli("add-topic", "--name", "UPI")
        self.run_with_findings([{"title": "F", "topics": ["UPI"], "sources": ["https://a.com/1"]}])
        finding_id = self.studio.findings()[0]["id"]
        self.cli("new-story", "--title", "Will UPI stay free?", "--finding", finding_id)
        story = self.studio.stories()[0]
        self.assertEqual(story["findings"], [finding_id])
        self.assertFalse(story["researched"])

        opened = self.studio.story(story["id"])
        (self.ws / "stories" / story["id"] / "notes.md").write_text("Agent notes")  # agent writes meanwhile
        with self.assertRaises(RuntimeError):
            self.studio.update_story(story["id"], {"notes": "user text"}, opened["version"])
        fresh = self.studio.story(story["id"])
        saved = self.studio.update_story(story["id"], {"title": "Renamed"}, fresh["version"])
        self.assertEqual((saved["notes"], saved["title"]), ("Agent notes", "Renamed"))
        self.assertIn("researched", self.cli("status"))

        self.studio.delete_story(story["id"])
        self.assertEqual(self.studio.stories(), [])
        self.assertTrue(any((self.ws / "stories" / ".trash").iterdir()))

    def test_production_scripts_per_channel(self):
        self.cli("add-channel", "--name", "Explained", "--platform", "YouTube Shorts", "--language", "English")
        self.cli("add-channel", "--name", "Paisa WhatsApp", "--kind", "post", "--language", "Hindi")
        self.assertIn("Paisa WhatsApp", self.cli("channels"))
        story = self.studio.create_story("UPI Lite limit")
        self.cli("new-script", "--story", story["id"], "--channel", "explained")
        self.cli("new-script", "--story", story["id"], "--channel", "Paisa WhatsApp")  # by name
        with self.assertRaises(SystemExit):
            self.cli("new-script", "--story", story["id"], "--channel", "explained")  # one script per channel
        scripts = {s["channel"]: s for s in self.studio.scripts()}
        self.assertEqual(set(scripts), {"explained", "paisa-whatsapp"})
        script = scripts["explained"]
        self.assertEqual((script["title"], script["story"], script["stage"]), ("UPI Lite limit", story["id"], "script"))
        self.assertIn("no draft yet", self.cli("status"))

        opened = self.studio.script(script["id"])
        (self.ws / "scripts" / script["id"] / "script.md").write_text("Agent draft")
        with self.assertRaises(RuntimeError):
            self.studio.update_script(script["id"], {"text": "user text"}, opened["version"])
        saved = self.studio.update_script(script["id"], {"stage": "published", "published_url": "youtube.com/shorts/x"})
        self.assertEqual((saved["text"], saved["published_url"]), ("Agent draft", "https://youtube.com/shorts/x"))
        with self.assertRaises(ValueError):
            self.studio.update_script(script["id"], {"stage": "nope"})
        with self.assertRaises(SystemExit):
            self.cli("add-channel", "--name", "explained")  # names are unique
        with self.assertRaises(ValueError):
            studio.delete_channel(self.home, "explained")  # still used by a script
        self.studio.delete_script(script["id"])
        studio.delete_channel(self.home, "explained")
        self.assertEqual([c["id"] for c in studio.channels(self.home)], ["paisa-whatsapp"])

    def test_comments_are_read_in_text_order(self):
        studio.add_channel(self.home, {"name": "Shorts"})
        script = self.studio.create_script(self.studio.create_story("S")["id"], "shorts")
        text = "Hook line.\nThe middle.\nHook line.\nThe end."
        self.studio.update_script(script["id"], {"text": text})
        last = self.studio.add_comment(script["id"], "Punchier ending", "The end.")
        whole = self.studio.add_comment(script["id"], "Too long overall")
        second_hook = self.studio.add_comment(script["id"], "Cut the repeat", "Hook line.", text.rindex("Hook line."))
        first = self.studio.add_comment(script["id"], "Start with a number", "Hook line.", 0)
        order = [c["id"] for c in self.studio.script(script["id"])["comments"]]
        self.assertEqual(order, [first["id"], second_hook["id"], last["id"], whole["id"]])
        listed = self.cli("comments", "--script", script["id"])
        self.assertLess(listed.index("Start with a number"), listed.index("Punchier ending"))
        self.assertIn("on the whole script", listed)
        self.cli("resolve", "--script", script["id"], "--comment", first["id"], "--reply", "Opened with ₹5,000")
        self.assertNotIn("Start with a number", self.cli("comments", "--script", script["id"]))
        version = self.studio.script(script["id"])["version"]
        self.studio.add_comment(script["id"], "More")
        self.assertEqual(self.studio.script(script["id"])["version"], version)  # comments never conflict with edits
        with self.assertRaises(ValueError):
            self.studio.add_comment(script["id"], " ")

    def test_deleting_topic_untags_findings(self):
        self.cli("add-topic", "--name", "UPI")
        self.run_with_findings([{"title": "F", "topics": ["UPI"], "sources": ["https://a.com/1"]}])
        self.studio.delete_topic("upi")
        self.assertEqual(self.studio.findings()[0]["topics"], [])

    def test_scan_lists_new_feed_items_once(self):
        feed = self.root / "feed.xml"
        feed.write_text(RSS)
        self.cli("add-source", "--url", "https://example.com")
        data = json.loads((self.ws / "sources.json").read_text())
        data["sources"][0].update(feed=feed.as_uri(), feed_checked=True)
        (self.ws / "sources.json").write_text(json.dumps(data))
        first = self.cli("scan")
        self.assertIn("Rate cut announced", first)
        self.assertIn("Big news", first)
        self.assertNotIn("Rate cut announced", self.cli("scan"))

    def test_runs_must_check_every_approved_source(self):
        self.cli("add-topic", "--name", "UPI")
        self.cli("add-source", "--url", "https://rbi.org.in", "--note", "Press")
        self.cli("suggest-source", "--url", "https://npci.org.in", "--reason", "Primary data")
        self.cli("start-run")
        run_id = self.studio.runs()[-1]["id"]
        self.assertEqual(self.studio.runs()[-1]["sources"], ["rbi-org-in"])  # suggestions are not required
        with self.assertRaises(SystemExit):
            self.cli("finish-run", "--run", run_id)
        with self.assertRaises(SystemExit):
            self.cli("checked", "--run", run_id, "--source", "npci-org-in")
        self.cli("checked", "--run", run_id, "--source", "rbi-org-in", "--note", "1 new")
        self.assertIn("1/1 sources checked", self.cli("finish-run", "--run", run_id))
        # A failed run may finish without every check.
        self.cli("start-run")
        self.assertIn("failed", self.cli("finish-run", "--run", self.studio.runs()[-1]["id"], "--failed", "no network"))

    def test_source_suggestions(self):
        self.cli("suggest-source", "--url", "npci.org.in", "--reason", "Primary data")
        source = self.studio.sources()[0]
        self.assertEqual((source["status"], source["reason"]), ("suggested", "Primary data"))
        with self.assertRaises(SystemExit):
            self.cli("suggest-source", "--url", "https://npci.org.in/", "--reason", "again")
        self.studio.update_source(source["id"], {"status": "dismissed"})
        with self.assertRaises(SystemExit):
            self.cli("suggest-source", "--url", "https://npci.org.in", "--reason", "please")  # stays dismissed
        self.cli("add-source", "--url", "https://npci.org.in", "--note", "user wants it")  # the user can still add it
        self.assertEqual(self.studio.sources()[0]["status"], "approved")
        self.assertEqual(len(self.studio.sources()), 1)

    def test_findings_link_to_your_sources_and_can_be_dismissed(self):
        self.cli("add-topic", "--name", "UPI")
        self.cli("add-source", "--url", "https://rbi.org.in/press")
        self.run_with_findings([{"title": "Limit raised", "topics": ["UPI"],
                                 "sources": ["https://www.rbi.org.in/press/123", "https://rbi.org.in/other", "https://news.com/x"]}])
        finding = self.studio.findings()[0]
        self.assertEqual([s["source_id"] for s in finding["sources"]], ["rbi-org-in-press", None, None])
        self.studio.set_dismissed(finding["id"], True)
        self.assertIn("dismissed_at", self.studio.findings()[0])
        self.assertIn("Findings: 0", self.cli("status"))
        self.studio.set_dismissed(finding["id"], False)
        self.assertNotIn("dismissed_at", self.studio.findings()[0])

    def test_explainer_stories_link_topics(self):
        self.cli("add-topic", "--name", "Chips")
        self.cli("new-story", "--title", "How do chip fabs work?", "--topic", "chips")
        story = self.studio.stories()[0]
        self.assertEqual((story["topics"], story["findings"]), (["chips"], []))
        with self.assertRaises(SystemExit):
            self.cli("new-story", "--title", "x", "--topic", "nope")
        self.studio.delete_topic("chips")
        self.assertEqual(self.studio.stories()[0]["topics"], [])

    def test_projects(self):
        self.cli("new-project", "--name", "Pipe Gyaan")
        with self.assertRaises(SystemExit):
            self.cli("add-topic", "--name", "Pipes")  # two projects now: which one?
        self.cli("add-topic", "--name", "Pipes", "--project", "pipe gyaan")  # by name, any case
        self.cli("add-topic", "--name", "Other", "--project", "test-project")  # by ID
        pipe = studio.Studio(self.home / "projects" / "pipe-gyaan")
        self.assertEqual([t["name"] for t in pipe.topics()], ["Pipes"])
        self.assertEqual([t["name"] for t in self.studio.topics()], ["Other"])
        self.assertIn("Pipe Gyaan", self.cli("projects"))
        self.assertIn("Several projects", self.cli("status"))
        with self.assertRaises(SystemExit):
            self.cli("new-project", "--name", "pipe gyaan")

    def test_settings_validation(self):
        self.studio.update_settings({"name": "Explained", "schedule": {"times": ["19:00", "07:00", "07:00"]}})
        self.assertEqual(self.studio.settings()["schedule"], {"days": studio.DAYS, "times": ["07:00", "19:00"]})
        self.assertEqual(studio.describe_schedule(self.studio.settings()["schedule"]), "every day at 07:00 and 19:00")
        self.studio.update_settings({"schedule": {"times": ["07:00"], "days": ["fri", "Mon", "wed"]}})
        self.assertEqual(studio.describe_schedule(self.studio.settings()["schedule"]), "Mon, Wed, Fri at 07:00")
        self.cli("set-schedule", "--time", "08:15", "--day", "mon", "--day", "tue", "--day", "wed", "--day", "thu", "--day", "fri")
        self.assertIn("weekdays at 08:15", self.cli("status"))
        self.cli("set-schedule", "--off")
        self.assertIn("manual only", self.cli("status"))
        for bad in ({"schedule": {"times": ["7am"]}}, {"schedule": {"times": ["07:00"], "days": ["someday"]}}, {"name": " "}, {"owner_secret": "x"}):
            with self.assertRaises(ValueError):
                self.studio.update_settings(bad)

    def test_web_api(self):
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)

        def call(method, path, body=None, host="localhost", headers=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            sent = {"Host": host, **(headers if headers is not None else {"X-Vid-Studio": "1", "Content-Type": "application/json"})}
            connection.request(method, path, body=json.dumps(body) if body is not None else None, headers=sent)
            response = connection.getresponse()
            raw = response.read().decode()
            return response.status, (json.loads(raw) if raw.startswith(("{", "[")) else raw)

        self.assertEqual(call("GET", "/")[0], 200)
        projects = call("GET", "/api/projects")[1]
        self.assertEqual([c["name"] for c in projects["projects"]], ["Test Project"])
        self.assertEqual(call("POST", "/api/projects", {"name": "Second"})[1]["id"], "second")
        self.assertEqual(call("GET", "/api/p/nope/state")[0], 404)
        self.assertEqual(call("GET", "/api/health")[1], str(self.home))
        status, topic = call("POST", "/api/p/test-project/topics", {"name": "UPI", "description": "d"})
        self.assertEqual((status, topic["name"]), (200, "UPI"))
        self.assertEqual(call("POST", "/api/p/test-project/topics", {"name": ""})[0], 400)
        self.assertEqual(call("PUT", "/api/p/test-project/topics/nope", {"name": "x"})[0], 404)
        status, story = call("POST", "/api/p/test-project/stories", {"title": "S"})
        status, saved = call("PUT", f"/api/p/test-project/stories/{story['id']}", {"notes": "hi", "version": story["version"]})
        self.assertEqual((status, saved["notes"]), (200, "hi"))
        self.assertEqual(call("PUT", f"/api/p/test-project/stories/{story['id']}", {"notes": "x", "version": story["version"]})[0], 409)
        self.assertEqual(call("GET", "/api/p/test-project/stories/..%2f..%2fetc")[0], 404)
        status, linked = call("POST", "/api/p/test-project/stories", {"title": "E", "topics": [topic["id"]]})
        self.assertEqual(linked["topics"], [topic["id"]])
        status, channel = call("POST", "/api/channels", {"name": "Shorts", "language": "Hindi"})
        self.assertEqual((status, channel["kind"]), (200, "video"))
        self.assertEqual(call("PUT", "/api/channels/shorts", {"language": "Hinglish"})[1]["language"], "Hinglish")
        self.assertEqual(call("POST", "/api/channels", {"name": "X", "kind": "film"})[0], 400)
        status, script = call("POST", "/api/p/test-project/scripts", {"story": story["id"], "channel": "shorts"})
        self.assertEqual((status, script["title"]), (200, "S"))
        status, saved = call("PUT", f"/api/p/test-project/scripts/{script['id']}", {"text": "hi", "version": script["version"]})
        self.assertEqual((status, saved["text"]), (200, "hi"))
        status, comment = call("POST", f"/api/p/test-project/scripts/{script['id']}/comments", {"body": "Why?", "quote": "hi", "offset": 0})
        self.assertEqual(call("PUT", f"/api/p/test-project/scripts/{script['id']}/comments/{comment['id']}", {"resolved": True})[0], 200)
        self.assertEqual(call("DELETE", f"/api/p/test-project/scripts/{script['id']}/comments/{comment['id']}")[0], 200)
        self.assertEqual(call("DELETE", "/api/channels/shorts")[0], 400)  # in use
        # The UI sends deletes with an empty JSON body.
        temp = call("POST", "/api/p/test-project/topics", {"name": "Temp"})[1]
        self.assertEqual(call("DELETE", f"/api/p/test-project/topics/{temp['id']}", {})[0], 200)
        self.assertEqual(call("PUT", "/api/p/test-project/findings/nope", {"dismissed": True})[0], 404)
        self.assertEqual(call("PUT", "/api/p/test-project/sources/nope", {"status": "approved"})[0], 404)
        state = call("GET", "/api/p/test-project/state")[1]
        self.assertEqual([t["name"] for t in state["topics"]], ["UPI"])
        self.assertEqual([c["name"] for c in state["channels"]], ["Shorts"])
        # Requests from other sites, or writes without the custom header, are refused.
        self.assertEqual(call("GET", "/api/p/test-project/state", host="evil.example")[0], 403)
        self.assertEqual(call("POST", "/api/p/test-project/topics", {"name": "Y"}, headers={"Content-Type": "text/plain"})[0], 403)


if __name__ == "__main__":
    unittest.main()
