"""Configuration semantics used by every studio stage."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "skills/vid-studio"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        module("init_workspace").initialize(self.workspace)
        self.resolve = module("resolve_preferences").resolve

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, path, value):
        destination = self.workspace / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value))

    def profile(self, name, prefs, parent=None):
        self.write(f"profiles/{name}.json", {"id": name, "revision": 1, "status": "approved", "extends": parent, "preferences": prefs})

    def test_inheritance_override_clear_and_no_writes(self):
        self.profile("default", {"script": {"tone": "calm", "structure": ["hook", "explain", "close"]}, "research": {"preferred_sources": ["journals"]}})
        self.profile("science", {"script": {"tone": "analytical"}, "custom_series_rule": "show mechanism"}, "default")
        self.write("monitoring/topics.json", {"topics": [{"id": "energy", "profile_id": "science", "preferences": {"script": {"structure": ["finding", "mechanism"]}, "research": {"depth": "deep"}}}]})
        self.write("projects/episode/project.json", {"id": "episode", "topic_id": "energy", "overrides": {"research": {"preferred_sources": []}, "script": {"tone": None}, "deliverables": ["research"]}})
        before = {str(p): p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()}
        result = self.resolve(self.workspace, project_id="episode")
        prefs = result["preferences"]
        self.assertEqual(result["context"]["profile_id"], "science")
        self.assertEqual(prefs["script"]["structure"], ["finding", "mechanism"])
        self.assertIsNone(prefs["script"]["tone"])
        self.assertEqual(prefs["research"]["preferred_sources"], [])
        self.assertEqual(prefs["research"]["depth"], "deep")
        self.assertEqual(prefs["deliverables"], ["research"])
        self.assertEqual(prefs["custom_series_rule"], "show mechanism")
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.workspace.rglob("*") if p.is_file()})

    def test_routing_and_context_conflicts(self):
        self.profile("brand", {})
        self.profile("topic-profile", {})
        self.profile("project-profile", {})
        self.write("monitoring/sources.json", {"sources": [{"id": "feed", "profile_id": "brand"}]})
        self.write("monitoring/topics.json", {"topics": [{"id": "topic", "profile_id": "topic-profile"}]})
        self.assertEqual(self.resolve(self.workspace, source_id="feed")["context"]["profile_id"], "brand")
        self.assertEqual(self.resolve(self.workspace, topic_id="topic", source_id="feed")["context"]["profile_id"], "topic-profile")
        self.write("projects/episode/project.json", {"id": "episode", "topic_id": "topic", "profile_id": "project-profile", "overrides": {}})
        self.assertEqual(self.resolve(self.workspace, project_id="episode")["context"]["profile_id"], "project-profile")
        with self.assertRaises(ValueError):
            self.resolve(self.workspace, project_id="episode", profile_id="brand")
        with self.assertRaises(ValueError):
            self.resolve(self.workspace, project_id="episode", topic_id="different")

    def test_missing_cycle_policy_and_path_failures(self):
        with self.assertRaises(FileNotFoundError):
            self.resolve(self.workspace, profile_id="missing")
        self.profile("a", {}, "b")
        self.profile("b", {}, "a")
        with self.assertRaises(ValueError):
            self.resolve(self.workspace, profile_id="a")
        self.profile("bad", {"workflow": {"approval_required_at_every_stage": False}})
        with self.assertRaises(ValueError):
            self.resolve(self.workspace, profile_id="bad")
        with self.assertRaises(ValueError):
            self.resolve(self.workspace, profile_id="../outside")
        self.profile("wrong-renderer", {"video": {"renderer": "other"}})
        with self.assertRaises(ValueError):
            self.resolve(self.workspace, profile_id="wrong-renderer")

    def test_version_one_preserved_after_initializer(self):
        old = {"schema_version": 1, "audience": "engineers", "languages": ["Hindi"], "video": {"aspect_ratio": "9:16", "width": 2160, "height": 3840}, "topic_domain": "energy"}
        self.write("studio.json", old)
        module("init_workspace").initialize(self.workspace)
        result = self.resolve(self.workspace)
        self.assertIsNone(result["context"]["profile_id"])
        self.assertEqual(result["preferences"]["audience"], "engineers")
        self.assertEqual(result["preferences"]["script"]["languages"], ["Hindi"])
        self.assertEqual(result["preferences"]["video"]["width"], 2160)
        self.assertEqual(json.loads((self.workspace / "studio.json").read_text()), old)

    def test_video_shape_dimensions_and_deferred_settings(self):
        for video in ("portrait", {"width": 1920, "height": 1080}, {"width": True}, {"height": 0}, {"fps": "NaN"}, {"fps": False}, {"fps": "1/0"}):
            with self.subTest(video=video):
                self.profile("test", {"video": video})
                with self.assertRaises(ValueError):
                    self.resolve(self.workspace, profile_id="test")
        self.profile("test", {"video": None, "deliverables": ["research"]})
        self.assertIn("video", self.resolve(self.workspace, profile_id="test")["unresolved_preferences"])
        self.profile("test", {"video": {"width": 2160, "height": 3840, "fps": "30000/1001"}})
        self.assertEqual(self.resolve(self.workspace, profile_id="test")["preferences"]["video"]["fps"], "30000/1001")

    def test_frozen_resume_and_explicit_snapshot_revision(self):
        self.profile("default", {"script": {"structure": ["finding", "evidence"]}, "narration": {"enabled": False}, "captions": {"enabled": False}})
        state = {"id": "episode", "preferences_path": "preferences.json", "overrides": {}}
        self.write("projects/episode/project.json", state)
        original = self.resolve(self.workspace, project_id="episode")
        self.write("projects/episode/preferences.json", original)
        saved = (self.workspace / "projects/episode/preferences.json").read_bytes()
        self.profile("default", {"script": {"structure": ["question", "explanation"]}})
        helper = module("resolve_preferences")
        self.assertEqual(helper.load_snapshot(self.workspace, "episode"), original)
        proposed = self.resolve(self.workspace, project_id="episode")
        self.assertNotEqual(proposed["preferences"]["script"]["structure"], original["preferences"]["script"]["structure"])
        self.write("projects/episode/preferences/r2.json", proposed)
        state["preferences_path"] = "preferences/r2.json"
        self.write("projects/episode/project.json", state)
        self.assertEqual(helper.load_snapshot(self.workspace, "episode"), proposed)
        self.assertEqual((self.workspace / "projects/episode/preferences.json").read_bytes(), saved)
        state["preferences_path"] = "../../studio.json"
        self.write("projects/episode/project.json", state)
        with self.assertRaises(ValueError):
            helper.load_snapshot(self.workspace, "episode")

    def test_profile_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "external.json"
            target.write_text(json.dumps({"id": "external", "preferences": {}}))
            (self.workspace / "profiles/external.json").symlink_to(target)
            with self.assertRaises(ValueError):
                self.resolve(self.workspace, profile_id="external")


if __name__ == "__main__":
    unittest.main()
