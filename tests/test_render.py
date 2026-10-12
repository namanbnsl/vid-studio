"""End-to-end MP4 render. Slow and needs Chrome, ffmpeg, and the network (GSAP and fonts load from CDNs).

Run with: VID_STUDIO_RENDER_TEST=1 python3 -m unittest tests.test_render
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vid-studio" / "scripts"))
import render  # noqa: E402
import studio  # noqa: E402


@unittest.skipIf(os.name == "nt", "DevTools uses POSIX pipes")
class BrowserPipeTest(unittest.TestCase):
    def test_timeout_and_closed_browser_are_reported(self):
        read_fd, write_fd = os.pipe()
        browser = render.Browser.__new__(render.Browser)
        browser._reader = os.fdopen(read_fd, "rb", buffering=0)
        browser._buffer = b""
        try:
            with self.assertRaises(TimeoutError):
                browser._read_message(time.monotonic() + 0.05)
            os.write(write_fd, b'{"id":1}\0')
            self.assertEqual(browser._read_message(time.monotonic() + 1), {"id": 1})
            os.close(write_fd)
            write_fd = None
            with self.assertRaisesRegex(RuntimeError, "closed unexpectedly"):
                browser._read_message(time.monotonic() + 1)
        finally:
            browser._reader.close()
            if write_fd is not None:
                os.close(write_fd)


@unittest.skipUnless(os.environ.get("VID_STUDIO_RENDER_TEST") and not render.missing_tools() and shutil.which("ffprobe"),
                     "set VID_STUDIO_RENDER_TEST=1 with Chrome, ffmpeg and ffprobe installed")
class RenderTest(unittest.TestCase):
    def test_draft_render_matches_the_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            studio.main(["--workspace", str(home), "new-project", "--name", "Render"])
            studio.add_channel(home, {"name": "Shorts", "language": "English"})
            project = studio.Studio(home / "projects" / "render", home)
            script = project.create_script(project.create_story("Render")["id"], "shorts")
            image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ioAAAAASUVORK5CYII=")
            media = project.add_media(script["id"], image, "test.png", "Test illustration")
            text = f"## Hook\nTwo seconds.\nVisual: stat | 42% | Share\nImage: {media['path']} | Test illustration\nDuration: 2\n## End\nVisual: end | Bye | Follow\nDuration: 1.5"
            project.update_script(script["id"], {"text": text})
            studio.start_render(project, script["id"], "draft")
            worker = studio.RENDERS[f"{project.ws}:{script['id']}"]
            worker.join(timeout=90)
            self.assertFalse(worker.is_alive(), "The background render did not finish")
            self.assertEqual(project.script(script["id"])["video"]["status"], "done", project.script(script["id"])["video"])
            output = project.path("scripts", script["id"], "render", "video.mp4")
            probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)],
                                              capture_output=True, text=True, check=True).stdout)
            video = next(s for s in probe["streams"] if s["codec_type"] == "video")
            self.assertEqual((video["codec_name"], video["width"], video["height"]), ("h264", 720, 1280))
            self.assertAlmostEqual(float(probe["format"]["duration"]), 3.5, delta=0.1)
            self.assertTrue((output.parent / "poster.jpg").is_file())
            previous = output.read_bytes()
            project.delete_media(script["id"], media["file"])
            with self.assertRaisesRegex(RuntimeError, "Images could not load"):
                project.render_script(script["id"], "draft")
            self.assertEqual(project.script(script["id"])["video"]["status"], "failed")
            self.assertEqual(output.read_bytes(), previous)
            self.assertFalse((output.parent / "media" / media["file"]).exists())


if __name__ == "__main__":
    unittest.main()
