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
        self.cli("new-channel", "--name", "Test Channel")
        self.ws = self.home / "channels" / "test-channel"
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

    def test_scripts_attach_and_detect_conflicts(self):
        self.cli("add-topic", "--name", "UPI")
        self.run_with_findings([{"title": "F", "topics": ["UPI"], "sources": ["https://a.com/1"]}])
        finding_id = self.studio.findings()[0]["id"]
        self.cli("new-script", "--title", "Will UPI stay free?", "--finding", finding_id)
        script = self.studio.scripts()[0]
        self.assertEqual(script["findings"], [finding_id])
        self.assertFalse(script["drafted"])

        opened = self.studio.script(script["id"])
        (self.ws / "scripts" / script["id"] / "script.md").write_text("Agent draft")  # agent writes meanwhile
        with self.assertRaises(RuntimeError):
            self.studio.update_script(script["id"], {"script": "user text"}, opened["version"])
        fresh = self.studio.script(script["id"])
        saved = self.studio.update_script(script["id"], {"post": "*Post*"}, fresh["version"])
        self.assertEqual((saved["script"], saved["post"]), ("Agent draft", "*Post*"))
        self.assertIn("drafted", self.cli("status"))

        self.studio.delete_script(script["id"])
        self.assertEqual(self.studio.scripts(), [])
        self.assertTrue(any((self.ws / "scripts" / ".trash").iterdir()))

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

    def test_explainer_scripts_link_topics(self):
        self.cli("add-topic", "--name", "Chips")
        self.cli("new-script", "--title", "How do chip fabs work?", "--topic", "chips")
        script = self.studio.scripts()[0]
        self.assertEqual((script["topics"], script["findings"]), (["chips"], []))
        self.assertIn("material but no draft", self.cli("status"))
        with self.assertRaises(SystemExit):
            self.cli("new-script", "--title", "x", "--topic", "nope")
        self.studio.delete_topic("chips")
        self.assertEqual(self.studio.scripts()[0]["topics"], [])

    def test_channels(self):
        self.cli("new-channel", "--name", "Pipe Gyaan", "--language", "Hinglish")
        with self.assertRaises(SystemExit):
            self.cli("add-topic", "--name", "Pipes")  # two channels now: which one?
        self.cli("add-topic", "--name", "Pipes", "--channel", "pipe gyaan")  # by name, any case
        self.cli("add-topic", "--name", "Other", "--channel", "test-channel")  # by ID
        pipe = studio.Studio(self.home / "channels" / "pipe-gyaan")
        self.assertEqual([t["name"] for t in pipe.topics()], ["Pipes"])
        self.assertEqual([t["name"] for t in self.studio.topics()], ["Other"])
        self.assertEqual(pipe.settings()["language"], "Hinglish")
        self.assertIn("Pipe Gyaan", self.cli("channels"))
        self.assertIn("Several channels", self.cli("status"))
        with self.assertRaises(SystemExit):
            self.cli("new-channel", "--name", "pipe gyaan")

    def test_single_channel_workspace_is_migrated(self):
        old = self.root / "old"
        old.mkdir()
        (old / "studio.json").write_text(json.dumps({"name": "Old Channel"}))
        (old / "topics.json").write_text(json.dumps({"topics": [{"id": "a", "name": "A", "description": ""}]}))
        (old / "scripts" / "s1").mkdir(parents=True)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            studio.main(["--workspace", str(old), "status"])
        folder = old / "channels" / "old-channel"
        self.assertFalse((old / "studio.json").exists())
        self.assertEqual(studio.Studio(folder).topics()[0]["name"], "A")
        self.assertTrue((folder / "scripts" / "s1").is_dir())
        self.assertTrue((folder / "findings.json").is_file())  # missing files filled from templates
        self.assertIn("Old Channel", output.getvalue())

    def test_settings_validation(self):
        self.studio.update_settings({"name": "Explained", "schedule": {"times": ["19:00", "07:00", "07:00"]}})
        self.assertEqual(self.studio.settings()["schedule"]["times"], ["07:00", "19:00"])
        for bad in ({"schedule": {"times": ["7am"]}}, {"name": " "}, {"owner_secret": "x"}):
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
        channels = call("GET", "/api/channels")[1]
        self.assertEqual([c["name"] for c in channels["channels"]], ["Test Channel"])
        self.assertEqual(call("POST", "/api/channels", {"name": "Second"})[1]["id"], "second")
        self.assertEqual(call("GET", "/api/c/nope/state")[0], 404)
        self.assertEqual(call("GET", "/api/health")[1], str(self.home))
        status, topic = call("POST", "/api/c/test-channel/topics", {"name": "UPI", "description": "d"})
        self.assertEqual((status, topic["name"]), (200, "UPI"))
        self.assertEqual(call("POST", "/api/c/test-channel/topics", {"name": ""})[0], 400)
        self.assertEqual(call("PUT", "/api/c/test-channel/topics/nope", {"name": "x"})[0], 404)
        status, script = call("POST", "/api/c/test-channel/scripts", {"title": "S"})
        status, saved = call("PUT", f"/api/c/test-channel/scripts/{script['id']}", {"script": "hi", "version": script["version"]})
        self.assertEqual((status, saved["script"]), (200, "hi"))
        self.assertEqual(call("PUT", f"/api/c/test-channel/scripts/{script['id']}", {"script": "x", "version": script["version"]})[0], 409)
        self.assertEqual(call("GET", "/api/c/test-channel/scripts/..%2f..%2fetc")[0], 404)
        status, linked = call("POST", "/api/c/test-channel/scripts", {"title": "E", "topics": [topic["id"]]})
        self.assertEqual(linked["topics"], [topic["id"]])
        self.assertEqual(call("PUT", "/api/c/test-channel/findings/nope", {"dismissed": True})[0], 404)
        self.assertEqual(call("PUT", "/api/c/test-channel/sources/nope", {"status": "approved"})[0], 404)
        state = call("GET", "/api/c/test-channel/state")[1]
        self.assertEqual([t["name"] for t in state["topics"]], ["UPI"])
        # Requests from other sites, or writes without the custom header, are refused.
        self.assertEqual(call("GET", "/api/c/test-channel/state", host="evil.example")[0], 403)
        self.assertEqual(call("POST", "/api/c/test-channel/topics", {"name": "Y"}, headers={"Content-Type": "text/plain"})[0], 403)


if __name__ == "__main__":
    unittest.main()
