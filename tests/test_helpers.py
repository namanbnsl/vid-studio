"""Behavioral checks for the shipped helpers. Run: python3 -m unittest discover -s tests."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "skills/vid-studio/scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkspaceTests(unittest.TestCase):
    def test_initialization_preserves_edits_and_starts_unapproved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "studio"
            initializer = load("init_workspace")
            first = initializer.initialize(root)
            self.assertTrue(first["created"])
            config = json.loads((root / "studio.json").read_text())
            self.assertEqual(config["setup_status"], "draft")
            self.assertEqual(config["tools"]["renderer"], "hyperframes")
            self.assertIn("preview", config["workflow"]["stages"])
            self.assertFalse(config["workflow"]["auto_publish"])
            self.assertEqual(json.loads((root / "setup-approval.json").read_text())["records"], [])
            (root / "brand/frame.md").write_text("Approved user-owned design")
            second = initializer.initialize(root)
            self.assertEqual(second["created"], [])
            self.assertEqual((root / "brand/frame.md").read_text(), "Approved user-owned design")

    def test_symlink_cannot_redirect_writes_outside_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "studio"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "brand").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                load("init_workspace").initialize(root)
            self.assertEqual(list(outside.iterdir()), [])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/ffprobe unavailable")
class ExportTests(unittest.TestCase):
    def test_container_duration_cannot_hide_short_video_or_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            verify = load("verify_export").verify
            for picture, sound in [(1, 3), (3, 1)]:
                video = Path(directory) / f"coverage-{picture}-{sound}.mp4"
                subprocess.run([
                    "ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c=navy:s=180x320:r=30:d={picture}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={sound}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video),
                ], check=True)
                self.assertFalse(verify(video, 180, 320, 30, 3, require_audio=True, decode=True)["ok"])
                if picture == 3:
                    self.assertTrue(verify(video, 180, 320, 30, 3, require_audio=True, audio_duration=1)["ok"])

    def test_decode_and_reject_wrong_format_or_missing_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "test.mp4"
            subprocess.run([
                "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=navy:s=180x320:r=30:d=1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video),
            ], check=True)
            verify = load("verify_export").verify
            result = verify(video, 180, 320, 30, 1, decode=True)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["decode"], "passed")
            self.assertEqual(result["visual_review"], "pending")
            self.assertFalse(verify(video, 1080, 1920, 30, 1)["ok"])
            self.assertFalse(verify(video, 180, 320, 60, 1)["ok"])
            self.assertFalse(verify(video, 180, 320, 30, 5)["ok"])
            self.assertFalse(verify(video, 180, 320, 30, 1, require_audio=True)["ok"])


if __name__ == "__main__":
    unittest.main()
