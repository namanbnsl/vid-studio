import contextlib
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from unittest import mock
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

    def test_hindi_channels_start_with_devanagari_fonts(self):
        if not (studio.SCENES_DIR / "presets" / f"{studio.HINDI_PRESET}.json").is_file():
            self.skipTest("scene presets not present")
        studio.add_channel(self.home, {"name": "Hindi Shorts", "language": "Hindi"})
        design = studio.channel_design(self.home, "hindi-shorts")
        self.assertEqual(design["preset"], studio.HINDI_PRESET)
        studio.save_design(self.home, "hindi-shorts", design | {"radius": 10})  # valid as it comes
        saved = studio.save_design(self.home, "hindi-shorts", {"colors": {"accent": "#123456"}})
        self.assertEqual(saved["preset"], design["preset"])
        self.assertEqual(saved["fonts"], design["fonts"])
        self.assertEqual(saved["colors"]["accent"], "#123456")

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

    def production_assets(self):
        assets = self.root / "scene-assets"
        assets.mkdir()
        for key, path in {"SCENES_DIR": assets, "PRESETS_DIR": assets / "presets", "FONT_CATALOG": assets / "fonts.json",
                          "VOICE_DEFAULT_PATH": self.root / "voice-default.json"}.items():
            patcher = mock.patch.object(studio, key, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        return assets

    def production_script(self, kind="video", language="English"):
        studio.add_channel(self.home, {"name": "Production", "kind": kind, "language": language})
        return self.studio.create_script(self.studio.create_story("A video")["id"], "production")

    def test_scene_spoken_words_and_duration(self):
        text = """# Ignore this title
Ignore this preamble.
## Hindi hook
**यह** _आज_ `नया` नियम है अब — । [UPI Lite](https://example.com) [1] [1, 2] [1–3]
- **VISUAL:** stat | ₹5,000 | Wallet | was ₹2,000
*Text:* ₹2,000 → ₹5,000
- **Note:** Check the source.
## Hinglish
UPI Lite की limit अब ₹5,000 है.
## Empty
Visual: end | Follow | Subscribe
"""
        scenes = studio.parse_scenes(text)
        self.assertEqual(len(scenes), 3)
        self.assertEqual(scenes[0], {"beat": "Hindi hook", "type": "stat", "duration": 3.0,
                                   "vo": "यह आज नया नियम है अब — । UPI Lite", "text": "₹2,000 → ₹5,000",
                                   "data": {"value": "₹5,000", "label": "Wallet", "context": "was ₹2,000"},
                                   "note": "Check the source."})
        self.assertEqual(studio.word_count(scenes[0]["vo"]), 8)
        self.assertEqual(scenes[1]["duration"], 2.6)
        self.assertEqual(scenes[1]["type"], "text")
        self.assertEqual(scenes[1]["data"]["text"], scenes[1]["vo"])
        self.assertEqual(scenes[2]["duration"], 1.5)
        self.assertEqual(studio.total_duration(scenes), 7.1)
        self.assertEqual(studio.parse_scenes(text, 80)[0]["duration"], 6)
        self.assertEqual(studio.parse_scenes("No beats"), [])
        self.assertEqual(studio.parse_scenes("## Short\nHi")[0]["duration"], 1.5)
        for bad in (0, -1, True, float("nan")):
            with self.assertRaises(ValueError):
                studio.parse_scenes(text, bad)

    def test_scene_pipe_fields_and_unknown_types(self):
        examples = {
            "title | A | B | C": ("title", {"title": "A", "subtitle": "B", "kicker": "C"}),
            "bars | Payments | Before: cap: ₹500 | Now: ₹1,000 | Empty: | Unpaired":
                ("bars", {"title": "Payments", "items": [{"label": "Before: cap", "value": "₹500"},
                                                          {"label": "Now", "value": "₹1,000"},
                                                          {"label": "Empty:", "value": ""}, {"label": "Unpaired", "value": ""}]}),
            "compare | Limits | Before: wallet: ₹2,000 | Now: ₹5,000":
                ("compare", {"title": "Limits", "items": [{"label": "Before: wallet", "value": "₹2,000"}, {"label": "Now", "value": "₹5,000"}]}),
            "timeline | Changes | 2024: First: launched | 2025: Expanded":
                ("timeline", {"title": "Changes", "items": [{"date": "2024", "label": "First: launched"}, {"date": "2025", "label": "Expanded"}]}),
            "list | Who | One | Two": ("list", {"title": "Who", "items": ["One", "Two"]}),
            "quote | The words | RBI": ("quote", {"quote": "The words", "source": "RBI"}),
            "text | Punchline": ("text", {"text": "Punchline"}),
            "image | A phone | https://example.com/phone.png": ("image", {"description": "A phone", "url": "https://example.com/phone.png", "credit": ""}),
            "end | Follow": ("end", {"title": "Follow", "cta": ""}),
            "chart | A custom scene | keep all fields": ("image", {"description": "chart | A custom scene | keep all fields", "url": "", "credit": ""}),
        }
        for visual, (kind, data) in examples.items():
            with self.subTest(visual=visual):
                scene = studio.parse_scenes(f"## Beat\nHello.\nVisual: {visual}")[0]
                self.assertEqual((scene["type"], scene["data"]), (kind, data))
        for label in ("Visual:", "*Visual:*", "**Visual:**", "**Visual**:", "- vIsUaL:"):
            with self.subTest(label=label):
                self.assertEqual(studio.parse_scenes(f"## Beat\n{label} stat | 42")[0]["type"], "stat")

    def test_scene_image_source_and_duration_cues(self):
        text = ("## Hook\nOne two three four.\nVisual: stat | 42% | Share\n"
                "Image: media/tap.jpg | Photo: A / Wikimedia Commons, CC BY 4.0\n- **Source:** RBI, 1 Oct 2026\nDuration: 4.25s\n"
                "## Hero\nVisual: image | A sensor tap | media/hero.png | Photo: B\nDuration: 90\n"
                "## Plain\nWords here.\nImage: https://example.com/x.jpg\nDuration: soon\n")
        hook, hero, plain = studio.parse_scenes(text, 160)
        self.assertEqual(hook["image"], {"src": "media/tap.jpg", "credit": "Photo: A / Wikimedia Commons, CC BY 4.0"})
        self.assertEqual((hook["source"], hook["duration"]), ("RBI, 1 Oct 2026", 4.3))
        self.assertEqual(hero["data"], {"description": "A sensor tap", "url": "media/hero.png", "credit": "Photo: B"})
        self.assertEqual((hero["duration"], "image" in hero, "source" in hero), (60.0, False, False))
        self.assertEqual(plain["image"], {"src": "https://example.com/x.jpg", "credit": ""})
        self.assertEqual(plain["duration"], 1.5)

    def test_script_media_export_and_video_status(self):
        assets = self.production_assets()
        for name in ("engine.js", "engine.css"):
            (assets / name).write_text("/* engine */")
        (assets / "composition.html").write_text('<div data-width="1080" data-height="1920"></div><script>__VID_SCENES_JSON__ __VID_DESIGN_JSON__</script>')
        script = self.production_script()
        jpeg, png = b"\xff\xd8\xff\xe0" + b"0" * 64, b"\x89PNG\r\n\x1a\n" + b"0" * 64
        item = self.studio.add_media(script["id"], jpeg, "Sensor Tap.JPG", "Photo: A", "https://example.com/page")
        self.assertEqual((item["file"], item["path"], item["credit"]), ("sensor-tap.jpg", "media/sensor-tap.jpg", "Photo: A"))
        self.assertEqual(self.studio.add_media(script["id"], png, "sensor tap.png")["file"], "sensor-tap-2.png")
        for bad in (b"GIF89a....", b"<svg></svg>", b""):
            with self.assertRaises(ValueError):
                self.studio.add_media(script["id"], bad, "x.jpg")
        with mock.patch.object(studio, "MAX_MEDIA_BYTES", 10), self.assertRaises(ValueError):
            self.studio.add_media(script["id"], jpeg, "big.jpg")
        self.assertEqual([m["file"] for m in self.studio.script(script["id"])["media"]], ["sensor-tap.jpg", "sensor-tap-2.png"])
        for bad in ("../script.json", "sensor-tap.gif", "missing.jpg"):
            with self.assertRaises(KeyError):
                self.studio.delete_media(script["id"], bad)
        self.studio.delete_media(script["id"], "sensor-tap-2.png")
        self.assertEqual(len(self.studio.media(script["id"])), 1)

        text = "## Hook\nA fact.\nVisual: stat | 5% | Rate\nImage: media/sensor-tap.jpg | Photo: A\n## Show it\nVisual: image | The product\n## End\nVisual: end | Bye"
        script = self.studio.update_script(script["id"], {"text": text})
        self.assertEqual(script["video"]["status"], "none")
        self.assertEqual(script["video"]["placeholders"], ["Show it"])
        folder = self.studio.export_script(script["id"])
        self.assertEqual((folder / "media" / "sensor-tap.jpg").read_bytes(), jpeg)
        self.assertIn("media/sensor-tap.jpg", (folder / "index.html").read_text())
        # A finished render is stale once the scenes, the look, or the photos change.
        (folder / "video.mp4").write_bytes(b"mp4")
        fingerprint = studio.media_fingerprint(self.studio.path("scripts", script["id"]), script["scenes"], studio.channel_design(self.home, "production"))
        studio.save(folder / "render.json", {"status": "done", "fingerprint": fingerprint, "finished": "now"})
        video = self.studio.script(script["id"])["video"]
        self.assertEqual((video["status"], video["ready"], video["stale"]), ("done", True, False))
        self.studio.update_script(script["id"], {"text": text.replace("5%", "6%")})
        self.assertTrue(self.studio.script(script["id"])["video"]["stale"])
        studio.save(folder / "render.json", {"status": "rendering", "pid": 2 ** 22 + 12345, "fingerprint": fingerprint})
        video = self.studio.script(script["id"])["video"]
        self.assertEqual((video["status"], video["error"]), ("failed", "The render stopped before it finished"))
        self.assertEqual(self.studio.scripts()[0]["video"], {"status": "failed", "ready": True, "stale": True})

    def test_media_cli_and_image_search_output(self):
        script = self.production_script()
        image = self.root / "photo.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
        out = self.cli("--project", "test-project", "media", "--script", script["id"], "--add", str(image), "--credit", "AI-generated illustration")
        self.assertIn("Saved media/photo.png", out)
        self.assertIn("Image: media/photo.png | AI-generated illustration", out)
        self.assertIn("media/photo.png · AI-generated illustration", self.cli("media", "--script", script["id"]))
        self.assertIn("Removed media/photo.png", self.cli("media", "--script", script["id"], "--remove", "photo.png"))
        commons = {"query": {"pages": {
            "1": {"index": 2, "title": "File:Tap.jpg", "imageinfo": [{"width": 2000, "height": 3000, "thumburl": "https://upload.example/tap.jpg?utm_source=x",
                  "descriptionurl": "https://commons.example/Tap", "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}, "Artist": {"value": "<a href='x'>Jane &amp; Co</a>"}}}]},
            "2": {"index": 1, "title": "File:NC.jpg", "imageinfo": [{"width": 2000, "height": 3000, "extmetadata": {"LicenseShortName": {"value": "CC BY-NC 4.0"}}}]},
            "3": {"index": 3, "title": "File:Wide.jpg", "imageinfo": [{"width": 3000, "height": 2000, "extmetadata": {"LicenseShortName": {"value": "CC0"}}}]}}}}
        openverse = {"results": [{"title": "Tap", "url": "https://flickr.example/t.jpg", "creator": "Sam", "license": "by", "license_version": "2.0",
                                  "source": "flickr", "foreign_landing_url": "https://flickr.example/p", "width": 1024, "height": 1536}]}
        replies = {"commons.wikimedia.org": commons, "api.openverse.org": openverse}
        with mock.patch.object(studio, "fetch", lambda url, timeout=25: (json.dumps(next(v for k, v in replies.items() if k in url)).encode(), "application/json", url)):
            out = self.cli("images", "sink tap", "--orientation", "tall")
        self.assertIn("1. Tap.jpg · 2000×3000 · CC BY-SA 4.0", out)
        self.assertIn("credit: Photo: Jane & Co / Wikimedia Commons, CC BY-SA 4.0", out)
        self.assertIn("url: https://upload.example/tap.jpg\n", out)
        self.assertNotIn("NC.jpg", out)
        self.assertNotIn("Wide.jpg", out)
        self.assertIn("credit: Photo: Sam / Flickr, CC BY 2.0", out)

    def test_image_cue_satisfies_placeholder_and_deleted_files_are_reported(self):
        script = self.production_script()
        image = self.studio.add_media(script["id"], b"\xff\xd8\xff" + b"0" * 64, "hero.jpg")
        saved = self.studio.update_script(script["id"], {"text": f"## Hero\nVisual: image | A tap\nImage: {image['path']}"})
        self.assertEqual(saved["video"]["placeholders"], [])
        self.studio.delete_media(script["id"], image["file"])
        self.assertEqual(self.studio.script(script["id"])["video"]["placeholders"], ["Hero"])

    def test_background_render_setup_failure_is_visible(self):
        import render
        script = self.production_script()
        self.studio.update_script(script["id"], {"text": "## Hook\nA fact."})
        with mock.patch.object(render, "missing_tools", return_value=[]), mock.patch.object(studio.Studio, "export_script", side_effect=OSError("Export failed")):
            studio.start_render(self.studio, script["id"])
            worker = studio.RENDERS[f"{self.studio.ws}:{script['id']}"]
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
        video = self.studio.script(script["id"])["video"]
        self.assertEqual((video["status"], video["error"]), ("failed", "Export failed"))

    def test_render_requires_tools_and_beats(self):
        script = self.production_script()
        with self.assertRaises(ValueError):
            self.studio.render_script(script["id"])
        self.studio.update_script(script["id"], {"text": "## Hook\nHello there"})
        import render
        with mock.patch.object(render, "missing_tools", lambda: ["ffmpeg (install it)"]), self.assertRaises(RuntimeError) as caught:
            self.studio.render_script(script["id"])
        self.assertIn("ffmpeg (install it)", str(caught.exception))

    def test_design_defaults_presets_validation_and_channel_paths(self):
        assets = self.production_assets()
        studio.add_channel(self.home, {"name": "Shorts"})
        self.assertEqual(studio.channel_design(self.home, "shorts"), studio.DEFAULT_DESIGN)
        self.assertEqual(studio.presets()[0]["id"], "bold-explainer")
        studio.save(assets / "presets" / "quiet.json", {"id": "quiet", "name": "A quiet look", "description": "Calm",
                                                       "design": {"colors": {"accent": "#abc"}, "motion": {"energy": "calm"}}})
        self.assertEqual([p["id"] for p in studio.presets()], ["quiet", "bold-explainer"])
        design = studio.save_design(self.home, "shorts", {"preset": "quiet", "colors": {"text": "#123456"}})
        self.assertEqual(design["colors"]["accent"], "#abc")
        self.assertEqual(design["motion"]["energy"], "calm")
        self.assertEqual(design["fonts"], studio.DEFAULT_DESIGN["fonts"])
        studio.save(self.home / "channels" / "shorts" / "design.json", {"preset": "quiet", "colors": {"text": "#FFF"}})
        self.assertEqual(studio.channel_design(self.home, "shorts")["colors"]["accent"], "#abc")
        studio.save(self.home / "channels" / "shorts" / "design.json", {"preset": "gone"})
        self.assertEqual(studio.channel_design(self.home, "shorts")["preset"], "bold-explainer")
        cases = [({"colors": {"accent": "yellow"}}, "colors.accent"), ({"colors": {"accent": "#12345"}}, "hex color"),
                 ({"type": {"scale": 2}}, "type.scale"), ({"type": {"tracking": -0.1}}, "type.tracking"),
                 ({"type": {"display_weight": 300}}, "display_weight"), ({"radius": 49}, "radius"),
                 ({"captions": {"max_words": 9}}, "max_words"), ({"captions": {"max_words": True}}, "integer"),
                 ({"aspect": "3:2"}, "aspect"), ({"motion": {"energy": "wild"}}, "motion.energy"),
                 ({"unknown": 1}, "Unknown design key"), ({"fonts": {"typo": "Anton"}}, "fonts key"),
                 ({"background": []}, "JSON object"), ({"preset": "missing"}, "preset id"),
                 ({"custom_css": "</STYLE><script>alert(1)"}, "CSS only"), ({"custom_css": "x" * 20001}, "20000"),
                 ({"custom_css": 2}, "must be text"), ({"radius": float("nan")}, "radius")]
        before = (self.home / "channels" / "shorts" / "design.json").read_bytes()
        for design, error in cases:
            with self.subTest(design=design), self.assertRaisesRegex(ValueError, error):
                studio.save_design(self.home, "shorts", design)
        self.assertEqual((self.home / "channels" / "shorts" / "design.json").read_bytes(), before)
        for bad in ("../shorts", "/tmp", "shorts/x", "shorts\\x", ".hidden"):
            with self.subTest(channel=bad), self.assertRaises(KeyError):
                studio.channel_design(self.home, bad)
        outside = self.root / "outside-channel"
        outside.mkdir()
        studio.add_channel(self.home, {"name": "Symlink"})
        (self.home / "channels" / "symlink").rmdir()
        (self.home / "channels" / "symlink").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            studio.save_voice(self.home, "symlink", {})
        studio.delete_channel(self.home, "shorts")
        self.assertFalse((self.home / "channels" / "shorts").exists())

    def test_design_font_catalog_and_devanagari(self):
        assets = self.production_assets()
        studio.save(assets / "fonts.json", {"fonts": [
            {"family": "Anton", "category": "display", "devanagari": False, "weights": [400]},
            {"family": "Mukta", "category": "sans-serif", "devanagari": True, "weights": [400, 800]},
            {"family": "JetBrains Mono", "category": "monospace", "devanagari": False, "weights": [400]},
        ]})
        for language in ("Hindi", "Hinglish"):
            channel = studio.add_channel(self.home, {"name": language, "language": language})
            with self.assertRaisesRegex(ValueError, "display.*Devanagari"):
                studio.save_design(self.home, channel["id"], {})
            with self.assertRaisesRegex(ValueError, "body.*Devanagari"):
                studio.save_design(self.home, channel["id"], {"fonts": {"display": "Mukta", "body": "Anton"}})
            saved = studio.save_design(self.home, channel["id"], {"fonts": {"display": "Mukta"}})
            self.assertEqual(saved["fonts"]["display"], "Mukta")
        studio.add_channel(self.home, {"name": "English"})
        studio.save_design(self.home, "english", {})
        with self.assertRaisesRegex(ValueError, "unknown family"):
            studio.save_design(self.home, "english", {"fonts": {"mono": "Missing"}})
        self.assertIn("Anton · display · devanagari no", self.cli("fonts"))
        self.assertIn("Mukta", self.cli("fonts", "--devanagari"))
        self.assertNotIn("Anton", self.cli("fonts", "--devanagari"))

    def test_voice_defaults_merge_and_validation(self):
        self.production_assets()
        studio.add_channel(self.home, {"name": "Shorts"})
        self.assertEqual(studio.channel_voice(self.home, "shorts"), studio.DEFAULT_VOICE)
        studio.save(studio.VOICE_DEFAULT_PATH, {"words_per_minute": 180, "tone": {"casual": 75}})
        voice = studio.save_voice(self.home, "shorts", {"tone": {"playful": 10}, "examples": [{"title": "A", "text": "B", "why": "C"}]})
        self.assertEqual(voice["tone"], {"playful": 10, "casual": 75, "intensity": 55})
        self.assertEqual(voice["words_per_minute"], 180)
        self.assertEqual(studio.channel_voice(self.home, "shorts"), voice)
        studio.save(self.home / "channels" / "shorts" / "voice.json", {"tone": {"intensity": 25}})
        self.assertEqual(studio.channel_voice(self.home, "shorts")["tone"], {"playful": 50, "casual": 75, "intensity": 25})
        bad = [{"length_seconds": 9}, {"length_seconds": 601}, {"words_per_minute": 79}, {"words_per_minute": 261},
               {"tone": {"playful": -1}}, {"tone": {"casual": 101}}, {"tone": {"other": 50}},
               {"hook_styles": ["fake"]}, {"hook_styles": "question"}, {"do": [1]}, {"dont": {}},
               {"persona": 7}, {"close": "x" * 4001}, {"examples": [{}]}, {"examples": ["text"]},
               {"unknown": "x"}, {"length_seconds": True}, {"words_per_minute": float("inf")}]
        for voice in bad:
            with self.subTest(voice=voice), self.assertRaises(ValueError):
                studio.save_voice(self.home, "shorts", voice)

    def test_script_production_data_and_version(self):
        self.production_assets()
        script = self.production_script()
        self.assertEqual((script["angles"], script["review"], script["scenes"], script["duration"]), ([], None, [], 0))
        script = self.studio.update_script(script["id"], {"text": "## Hook\nOne two three four five six seven eight"})
        self.assertEqual(script["duration"], 3)
        version = script["version"]
        studio.save_voice(self.home, "production", {"words_per_minute": 80})
        self.assertEqual(self.studio.scripts()[0]["duration"], 6)
        self.assertEqual(self.studio.script(script["id"])["version"], version)
        angles = [{"hook": "Question?", "angle": "Explain", "why": "Curiosity"}, {"hook": "Number", "angle": "Data", "why": "Specificity"}]
        saved = self.studio.save_angles(script["id"], {"angles": angles})
        self.assertEqual([a["id"] for a in saved], ["a1", "a2"])
        self.assertEqual([a["chosen"] for a in saved], [True, False])
        changed = self.studio.update_script(script["id"], {"chosen_angle": "a2"}, version)
        self.assertEqual([a["chosen"] for a in changed["angles"]], [False, True])
        self.assertEqual(changed["version"], version)
        self.assertEqual(changed["text"], script["text"])
        self.assertEqual(studio.load(self.ws / "scripts" / script["id"] / "angles.json")["angles"], changed["angles"])
        with self.assertRaises(KeyError):
            self.studio.update_script(script["id"], {"chosen_angle": "missing", "text": "Do not write"})
        for bad in ([angles[0]], angles * 4, [angles[0] | {"chosen": True}, angles[1] | {"chosen": True}],
                    [angles[0] | {"id": "same"}, angles[1] | {"id": "same"}], [angles[0] | {"chosen": 1}, angles[1]],
                    [angles[0] | {"why": 1}, angles[1]]):
            with self.subTest(angles=bad), self.assertRaises(ValueError):
                self.studio.save_angles(script["id"], bad)
        scores = {key: 8 for key in ("hook", "clarity", "retention", "specificity", "voice", "natural", "value", "accuracy")}
        review = self.studio.save_review(script["id"], {"scores": scores, "summary": "Strong", "notes": ["Check date"], "at": "ignored"})
        studio.parse_time(review["at"])
        self.assertEqual(self.studio.script(script["id"])["review"], review)
        self.assertEqual(self.studio.script(script["id"])["version"], version)
        for score in (0, 11, 8.5, True):
            with self.subTest(score=score), self.assertRaises(ValueError):
                self.studio.save_review(script["id"], review | {"scores": scores | {"hook": score}})
        for bad in (review | {"scores": {}}, review | {"notes": [1]}, review | {"summary": 1}):
            with self.assertRaises(ValueError):
                self.studio.save_review(script["id"], bad)
        post_channel = studio.add_channel(self.home, {"name": "Post", "kind": "post"})
        post = self.studio.create_script(script["story"], post_channel["id"])
        post = self.studio.update_script(post["id"], {"text": "## Heading\nOne two three"})
        self.assertEqual((post["scenes"], post["duration"]), ([], 0))

    def test_export_safe_json_and_assets(self):
        assets = self.production_assets()
        script = self.production_script()
        with self.assertRaisesRegex(RuntimeError, "Missing scene asset.*engine.js"):
            self.studio.export_script(script["id"])
        (assets / "engine.js").write_text("// engine")
        (assets / "engine.css").write_text(".scene{}")
        (assets / "composition.html").write_text('<title>__VID_TITLE__</title><script id="design">__VID_DESIGN_JSON__</script><script id="scenes">__VID_SCENES_JSON__</script>')
        text = "## Hook\nHello.\nVisual: image | </script><script>& danger __VID_TITLE__ | https://example.com?a=1&b=2"
        script = self.studio.update_script(script["id"], {"title": '<Title & "quote">', "text": text})
        studio.save_design(self.home, "production", {"logo": {"text": "</script>&\u2028\u2029"}})
        folder = self.studio.export_script(script["id"])
        self.assertEqual(folder, self.ws / "scripts" / script["id"] / "render")
        exported = (folder / "index.html").read_text()
        self.assertIn("&lt;Title &amp; &quot;quote&quot;&gt;", exported)
        self.assertNotIn("</script><script>& danger", exported)
        self.assertIn("\\u003c/script\\u003e\\u0026\\u2028\\u2029", exported)
        self.assertIn("__VID_TITLE__", exported)  # user data is substituted only once
        import re
        payloads = re.findall(r'<script id="[^"]+">(.*?)</script>', exported)
        self.assertEqual(json.loads(payloads[0]), studio.channel_design(self.home, "production"))
        self.assertEqual(json.loads(payloads[1]), script["scenes"])
        self.assertEqual((folder / "engine.js").read_bytes(), (assets / "engine.js").read_bytes())
        self.assertEqual((folder / "engine.css").read_bytes(), (assets / "engine.css").read_bytes())
        self.assertIn("npx hyperframes preview", self.cli("export", "--script", script["id"], "--out", str(self.root / "export")))
        post_channel = studio.add_channel(self.home, {"name": "Post", "kind": "post"})
        post = self.studio.create_script(script["story"], post_channel["id"])
        with self.assertRaisesRegex(ValueError, "video channel"):
            self.studio.export_script(post["id"])

    def test_production_cli_output(self):
        self.production_assets()
        script = self.production_script()
        self.assertEqual(json.loads(self.cli("design", "--channel", "Production")), studio.DEFAULT_DESIGN)
        self.assertIn("changed colors", self.cli("design", "--channel", "production", "--file", "-", stdin='{"colors":{"accent":"#ABC"}}'))
        self.assertIn("changed words_per_minute", self.cli("voice", "--channel", "Production", "--file", "-", stdin='{"words_per_minute":120}'))
        self.assertEqual(json.loads(self.cli("voice", "--channel", "production"))["words_per_minute"], 120)
        self.assertIn("bold-explainer · Bold Explainer", self.cli("presets"))
        script = self.studio.update_script(script["id"], {"text": "## Hook\n" + "word " * 30 + "\nText: one two three four five six seven eight nine\nVisual: stat | 42"})
        output = self.cli("scenes", "--script", script["id"])
        self.assertIn("1. Hook · stat · 15.0s", output)
        self.assertIn("Total 15.0s (target 60s)", output)
        for warning in ("over 12s", "more than 8 words", "missing an end scene", "more than 10% off"):
            self.assertIn(warning, output)
        self.assertEqual(json.loads(self.cli("scenes", "--script", script["id"], "--json")), script["scenes"])
        angles = {"angles": [{"hook": "A", "angle": "B", "why": "C"}, {"hook": "D", "angle": "E", "why": "F"}]}
        self.assertIn("Saved 2 angles", self.cli("angles", "--script", script["id"], "--file", "-", stdin=json.dumps(angles)))
        review = {"scores": {key: 7 for key in ("hook", "clarity", "retention", "specificity", "voice", "natural", "value", "accuracy")}, "summary": "Good", "notes": []}
        self.assertIn("hook 7/10", self.cli("review", "--script", script["id"], "--file", "-", stdin=json.dumps(review)))
        status = self.cli("status")
        self.assertIn("look bold-explainer", status)
        self.assertIn("15.0s", status)
        studio.create_project(self.home, "Second")
        self.assertEqual(json.loads(self.cli("design", "--channel", "Production"))["colors"]["accent"], "#ABC")
        file = self.root / "voice-settings.json"
        file.write_text('{"length_seconds":90}')
        self.assertIn("changed length_seconds", self.cli("voice", "--channel", "production", "--file", str(file)))
        with self.assertRaisesRegex(SystemExit, "Cannot read JSON"):
            self.cli("design", "--channel", "Production", "--file", "-", stdin="broken")

    def test_production_web_api_and_static_security(self):
        assets = self.production_assets()
        script = self.production_script()
        script = self.studio.update_script(script["id"], {"text": "## Hook\nOne two three four five six seven eight"})
        self.studio.save_angles(script["id"], [{"hook": "A", "angle": "B", "why": "C"}, {"hook": "D", "angle": "E", "why": "F"}])
        (assets / "presets").mkdir()
        studio.save(assets / "presets" / "sample.json", {"id": "sample", "name": "Sample", "description": "Test", "design": {}})
        extensions = {"js": "text/javascript", "css": "text/css", "html": "text/html", "json": "application/json",
                      "svg": "image/svg+xml", "woff2": "font/woff2", "png": "image/png"}
        for extension in extensions:
            (assets / f"asset.{extension}").write_bytes(b"{}" if extension == "json" else b"test asset")
        (assets / ".secret").write_text("secret")
        (assets / "hidden-link").symlink_to(assets / ".secret")
        (assets / "escape").symlink_to(self.root, target_is_directory=True)
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        def call(method, path, body=None, headers=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            try:
                sent = {"Host": "localhost", **(headers if headers is not None else {"X-Vid-Studio": "1", "Content-Type": "application/json"})}
                connection.request(method, path, body=json.dumps(body) if body is not None else None, headers=sent)
                response = connection.getresponse()
                raw = response.read()
                data = json.loads(raw) if response.getheader("Content-Type", "").startswith("application/json") else raw
                return response.status, data, dict(response.getheaders())
            finally:
                connection.close()

        status, design, _ = call("GET", "/api/channels/production/design")
        self.assertEqual((status, design), (200, studio.DEFAULT_DESIGN))
        status, design, _ = call("PUT", "/api/channels/production/design", {"colors": {"accent": "#abc"}})
        self.assertEqual((status, design["colors"]["accent"]), (200, "#abc"))
        self.assertEqual(design["aspect"], "9:16")
        self.assertEqual(call("GET", "/api/channels/production/design")[1], design)
        self.assertEqual(call("PUT", "/api/channels/production/design", {"radius": 100})[0], 400)
        self.assertEqual(call("GET", "/api/channels/nope/design")[0], 404)
        self.assertEqual(call("GET", "/api/channels/..%2foutside/design")[0], 404)
        self.assertEqual(call("GET", "/api/channels/production/voice")[1], studio.DEFAULT_VOICE)
        status, voice, _ = call("PUT", "/api/channels/production/voice", {"words_per_minute": 80, "tone": {"casual": 30}})
        self.assertEqual((status, voice["tone"]["casual"], voice["tone"]["playful"]), (200, 30, 50))
        self.assertEqual(call("GET", "/api/channels/production/voice")[1], voice)
        self.assertEqual(call("PUT", "/api/channels/production/voice", {"words_per_minute": 300})[0], 400)
        for path in ("/api/channels/production/design", "/api/channels/production/voice"):
            self.assertEqual(call("PUT", path, {}, headers={"Content-Type": "application/json"})[0], 403)
            self.assertEqual(call("PUT", path, {}, headers={"X-Vid-Studio": "1", "Content-Type": "text/plain"})[0], 403)
            self.assertEqual(call("PUT", path, [1, 2])[0], 400)
        self.assertEqual({p["id"] for p in call("GET", "/api/presets")[1]}, {"sample", "bold-explainer"})
        self.assertEqual(call("GET", "/api/fonts")[1], {"fonts": []})
        catalog = {"fonts": [{"family": "Mukta", "category": "sans-serif", "devanagari": True, "weights": [400]}]}
        studio.save(assets / "fonts.json", catalog)
        self.assertEqual(call("GET", "/api/fonts")[1], catalog)
        self.assertNotIn("design", call("GET", "/api/channels")[1][0])
        path = f"/api/p/test-project/scripts/{script['id']}"
        status, changed, _ = call("PUT", path, {"chosen_angle": "a2", "version": script["version"]})
        self.assertEqual(status, 200)
        self.assertEqual(changed["version"], script["version"])
        self.assertEqual(changed["text"], script["text"])
        self.assertEqual([a["chosen"] for a in changed["angles"]], [False, True])
        self.assertEqual(changed["duration"], 6)
        self.assertEqual(call("PUT", path, {"chosen_angle": "missing"})[0], 404)
        self.assertEqual(call("GET", "/api/p/test-project/state")[1]["scripts"][0]["duration"], 6)
        media = f"/api/p/test-project/scripts/{script['id']}/media"
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 16
        status, item, _ = call("POST", media, {"name": "My Photo.png", "data": "data:image/png;base64," + __import__("base64").b64encode(png).decode()})
        self.assertEqual((status, item["path"]), (200, "media/my-photo.png"))
        status, body, headers = call("GET", f"{media}/my-photo.png")
        self.assertEqual((status, body, headers["Content-Type"]), (200, png, "image/png"))
        self.assertEqual(call("POST", media, {"name": "x.png", "data": "not base64!"})[0], 400)
        self.assertEqual(call("POST", media, {"name": "x.svg", "data": "PHN2Zz4="})[0], 400)
        self.assertEqual(call("GET", f"{media}/..%2fscript.json")[0], 404)
        self.assertEqual(call("GET", f"{media}/missing.png")[0], 404)
        self.assertEqual(call("DELETE", f"{media}/my-photo.png")[1], {"ok": True})
        self.assertEqual(call("GET", f"/api/p/test-project/scripts/{script['id']}/video")[0], 404)
        import render
        with mock.patch.object(render, "missing_tools", lambda: ["ffmpeg"]):
            status, error, _ = call("POST", f"/api/p/test-project/scripts/{script['id']}/render", {})
        self.assertEqual((status, error["error"]), (409, "Rendering needs ffmpeg"))
        folder = self.studio.path("scripts", script["id"], "render")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "video.mp4").write_bytes(b"fake mp4")
        status, body, headers = call("GET", f"/api/p/test-project/scripts/{script['id']}/video")
        self.assertEqual((status, body, headers["Content-Type"]), (200, b"fake mp4", "video/mp4"))
        self.assertTrue(headers["Content-Disposition"].startswith('attachment; filename="a-video.mp4"'))
        for extension, content_type in extensions.items():
            with self.subTest(extension=extension):
                status, _, headers = call("GET", f"/scenes/asset.{extension}")
                self.assertEqual(status, 200)
                self.assertTrue(headers["Content-Type"].startswith(content_type))
                self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(call("GET", "/scenes/presets/sample.json")[0], 200)
        attempts = ["/scenes/../studio.py", "/scenes/%2e%2e/studio.py", "/scenes/%2e%2e%2fstudio.py",
                    "/scenes/%2Fetc/passwd", "/scenes//etc/passwd", "/scenes/..%5cstudio.py", "/scenes/.secret",
                    "/scenes/%2esecret", "/scenes/presets/../sample.json", "/scenes/escape/voice-default.json",
                    "/scenes/hidden-link", "/scenes/missing.js"]
        for path in attempts:
            with self.subTest(path=path):
                self.assertEqual(call("GET", path)[0], 404)

    def test_global_production_keeps_project_ownership(self):
        studio.add_channel(self.home, {"name": "Shared"})
        first_story = self.studio.create_story("Same story")
        first = self.studio.create_script(first_story["id"], "shared")
        second = studio.Studio(studio.create_project(self.home, "Second"), self.home)
        second_story = second.create_story("Same story")
        other = second.create_script(second_story["id"], "shared")
        self.assertEqual(first["id"], other["id"])  # globally unique IDs cannot be assumed
        overview = studio.production_overview(self.home)
        self.assertEqual({(s["project"], s["id"]) for s in overview["scripts"]},
                         {("test-project", first["id"]), ("second", other["id"])})
        self.assertEqual({s["project_name"] for s in overview["scripts"]}, {"Test Project", "Second"})
        self.assertEqual([c["id"] for c in overview["channels"]], ["shared"])
        self.assertTrue(all(s["story_title"] == "Same story" for s in overview["scripts"]))
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with contextlib.closing(http.client.HTTPConnection("127.0.0.1", server.server_port)) as connection:
            connection.request("GET", "/api/production", headers={"Host": "localhost"})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(len(json.loads(response.read())["scripts"]), 2)
            connection.request("PUT", f"/api/p/second/scripts/{other['id']}",
                               json.dumps({"title": "Second only", "stage": "ready"}),
                               {"Host": "localhost", "X-Vid-Studio": "1", "Content-Type": "application/json"})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())["stage"], "ready")
        self.assertEqual(self.studio.script(first["id"])["stage"], "script")
        self.assertEqual(self.studio.script(first["id"])["title"], "Same story")

    def test_global_production_without_research_projects(self):
        root = self.root / "empty-studio"
        studio.add_channel(root, {"name": "Independent"})
        overview = studio.production_overview(root)
        self.assertEqual(overview["projects"], [])
        self.assertEqual(overview["scripts"], [])
        self.assertEqual(overview["stories"], [])
        self.assertEqual(overview["channels"][0]["name"], "Independent")

    def test_web_api(self):
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
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
