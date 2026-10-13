"""Render an exported composition (index.html + engine) to MP4 on this machine.

Standard library only. Drives a local Chrome/Chromium/Edge over the DevTools pipe (no websockets, no
npm), seeks the composition's paused GSAP timeline frame by frame, and pipes the screenshots to ffmpeg.
Every frame is a pure function of its time, so the output is the same on every run.
"""

from __future__ import annotations

import base64
import functools
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CHROME_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "microsoft-edge", "msedge"]
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def find_chrome() -> str | None:
    if os.environ.get("VID_STUDIO_CHROME"):
        return os.environ["VID_STUDIO_CHROME"]
    for name in CHROME_NAMES:
        if shutil.which(name):
            return shutil.which(name)
    for path in CHROME_PATHS:
        if Path(path).is_file():
            return path
    # Playwright's bundled Chromium, if the user has it
    cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or Path.home() / ".cache" / "ms-playwright")
    for candidate in sorted(cache.glob("chromium-*/chrome-*/chrome"), reverse=True):
        if candidate.is_file():
            return str(candidate)
    return None


def find_ffmpeg() -> str | None:
    return os.environ.get("VID_STUDIO_FFMPEG") or shutil.which("ffmpeg")


def missing_tools() -> list[str]:
    """What this machine lacks for rendering, as install hints (empty when ready)."""
    hints = []
    if os.name == "nt":
        hints.append("Rendering runs on macOS and Linux (on Windows, use WSL)")
    if not find_chrome():
        hints.append("Google Chrome or Chromium (or set VID_STUDIO_CHROME to its path)")
    if not find_ffmpeg():
        hints.append("ffmpeg (macOS: `brew install ffmpeg`; Ubuntu: `sudo apt install ffmpeg`)")
    return hints


class Browser:
    """A headless browser driven over --remote-debugging-pipe (fd 3 in, fd 4 out)."""

    def __init__(self, chrome: str, width: int, height: int, extra_args: tuple = ()):
        self.profile = tempfile.mkdtemp(prefix="vid-render-")
        to_chrome_r, self._to_chrome = os.pipe()
        self._from_chrome, from_chrome_w = os.pipe()

        args = [chrome, "--headless=new", "--remote-debugging-pipe", f"--user-data-dir={self.profile}",
                "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--mute-audio",
                "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows", "--disable-extensions", "--font-render-hinting=none",
                "--force-color-profile=srgb", f"--window-size={width},{height}", "--force-device-scale-factor=1",
                *extra_args, "about:blank"]
        # preexec_fn can deadlock when rendering from the threaded studio server. Remap the
        # DevTools descriptors in a fresh Python process, then replace it with Chrome.
        launcher = "import fcntl,os,sys; a=fcntl.fcntl(int(sys.argv[1]),fcntl.F_DUPFD,5); b=fcntl.fcntl(int(sys.argv[2]),fcntl.F_DUPFD,5); os.dup2(a,3); os.dup2(b,4); os.close(a); os.close(b); os.execv(sys.argv[3],sys.argv[3:])"
        try:
            self.process = subprocess.Popen([sys.executable, "-c", launcher, str(to_chrome_r), str(from_chrome_w), *args],
                                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                            pass_fds=(to_chrome_r, from_chrome_w))
        except BaseException:
            os.close(self._to_chrome)
            os.close(self._from_chrome)
            shutil.rmtree(self.profile, ignore_errors=True)
            raise
        finally:
            os.close(to_chrome_r)
            os.close(from_chrome_w)
        self._reader = os.fdopen(self._from_chrome, "rb", buffering=0)
        self._buffer = b""
        self._next_id = 0
        self.session = None

    def _read_message(self, deadline: float) -> dict:
        while b"\0" not in self._buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self._reader], [], [], remaining)[0]:
                raise TimeoutError("The browser did not respond before the deadline")
            chunk = self._reader.read(1 << 20)
            if not chunk:
                raise RuntimeError("The browser closed unexpectedly")
            self._buffer += chunk
        raw, self._buffer = self._buffer.split(b"\0", 1)
        return json.loads(raw)

    def send(self, method: str, params: dict | None = None, session: bool = True, timeout: float = 60) -> dict:
        self._next_id += 1
        message = {"id": self._next_id, "method": method, "params": params or {}}
        if session and self.session:
            message["sessionId"] = self.session
        os.write(self._to_chrome, json.dumps(message).encode() + b"\0")
        deadline = time.monotonic() + timeout
        while True:
            reply = self._read_message(deadline)
            if reply.get("id") == self._next_id:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error'].get('message')}")
                return reply.get("result", {})
            if time.monotonic() > deadline:
                raise TimeoutError(f"{method} timed out")

    def open(self, url: str, width: int, height: int) -> None:
        target = self.send("Target.createTarget", {"url": "about:blank"}, session=False)["targetId"]
        self.session = self.send("Target.attachToTarget", {"targetId": target, "flatten": True}, session=False)["sessionId"]
        self.send("Page.enable")
        self.send("Runtime.enable")
        self.send("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
        self.send("Page.navigate", {"url": url})

    def evaluate(self, expression: str, timeout: float = 60):
        result = self.send("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True}, timeout=timeout)
        if result.get("exceptionDetails"):
            raise RuntimeError(result["exceptionDetails"].get("exception", {}).get("description") or "Script error in the composition")
        return result.get("result", {}).get("value")

    def screenshot(self, width: int, height: int, quality: int) -> bytes:
        result = self.send("Page.captureScreenshot", {
            "format": "jpeg", "quality": quality, "optimizeForSpeed": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1}})
        return base64.b64decode(result["data"])

    def close(self, force: bool = False) -> None:
        if force and self.process.poll() is None:
            self.process.kill()
        elif self.process.poll() is None:
            try:
                self.send("Browser.close", session=False, timeout=5)
            except Exception:
                pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self._reader.close()
        for fd in (self._to_chrome,):
            try:
                os.close(fd)
            except OSError:
                pass
        shutil.rmtree(self.profile, ignore_errors=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve_folder(folder: Path) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(folder)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


READY_JS = """(() => { const d = document.documentElement, s = document.getElementById('stage');
    if (!d || !s) return null;
    return {ready: d.getAttribute('data-vid-ready'), error: d.getAttribute('data-vid-error'),
            width: s && +s.getAttribute('data-width'), height: s && +s.getAttribute('data-height'),
            duration: s && +s.getAttribute('data-duration'), fonts: s && s.getAttribute('data-fonts'),
            first: (window.__vidScenes && window.__vidScenes[0] && window.__vidScenes[0].duration) || 0,
            failedImages: [...document.querySelectorAll('.backdrop[data-failed] img')].map(i => i.getAttribute('src'))}; })()"""


def open_composition(url: str, scale: float = 1.0) -> tuple[Browser, dict]:
    """Start a browser on the composition and wait for fonts, images, measuring and fitting."""
    browser = Browser(find_chrome(), 1080, 1920)
    try:
        browser.open(url, 1080, 1920)
        info, deadline = None, time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                info = browser.evaluate(READY_JS)
            except RuntimeError:  # the page is still navigating
                info = None
            if info and (info.get("ready") or info.get("error")):
                break
            time.sleep(0.2)
        if not info or info.get("error"):
            raise RuntimeError(f"The composition failed to build: {info and info.get('error') or 'timed out'}")
        if not info.get("ready"):
            raise RuntimeError("The composition did not finish building within 60 seconds")
        if info.get("failedImages"):
            raise RuntimeError("Images could not load: " + ", ".join(info["failedImages"]) + ". Replace them before rendering.")
        browser.send("Emulation.setDeviceMetricsOverride", {"width": int(info["width"]), "height": int(info["height"]),
                                                            "deviceScaleFactor": scale, "mobile": False})
        browser.evaluate("document.body.style.margin='0'; window.scrollTo(0,0); true")
        return browser, info
    except BaseException:
        browser.close()
        raise


def default_workers() -> int:
    return max(1, min(4, (os.cpu_count() or 2) // 2))


def mix_voiceover(clips: list, duration: float, output: Path) -> Path:
    """One 48 kHz track from (start seconds, WAV path) clips, padded or cut to the video's length.

    Each clip is resampled on its own (providers differ), placed at its beat's start, and the mix is
    loudness-normalised for phones (about -16 LUFS, peaks under -1.5 dB).
    """
    if not find_ffmpeg():
        raise RuntimeError("Mixing the voiceover needs ffmpeg")
    if not clips:
        raise ValueError("No voiceover clips to mix")
    output = Path(output)
    inputs, chains = [], []
    for i, (start, path) in enumerate(clips):
        inputs += ["-i", str(path)]
        delay = max(0, round(float(start) * 1000))
        chains.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=mono,adelay={delay}:all=1[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    # Pad before loudnorm (padding after it comes up short), with margin; -t then cuts to the exact length.
    graph = ";".join(chains) + f";{mix}amix=inputs={len(clips)}:normalize=0:dropout_transition=0," \
        f"apad=whole_dur={float(duration) + 0.5:.3f},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[out]"
    done = subprocess.run([find_ffmpeg(), "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]",
                           "-t", f"{float(duration):.3f}", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(output)], capture_output=True, text=True)
    if done.returncode:
        raise RuntimeError(f"ffmpeg couldn't mix the voiceover: {done.stderr.strip()[-400:]}")
    return output


def render(folder: Path, output: Path, fps: int = 30, quality: str = "high", progress=None, poster: Path | None = None,
           workers: int | None = None, audio: Path | None = None) -> dict:
    """Render folder/index.html to output (MP4). progress(done_frames, total_frames) is called as frames land.

    Several browsers render interleaved frames in parallel; frames reach ffmpeg in order. With audio (a WAV
    as long as the video), that is the soundtrack; otherwise the MP4 gets a silent one, which platforms expect.
    """
    problems = missing_tools()
    if problems:
        raise RuntimeError("Rendering needs: " + "; ".join(problems))
    folder, output = Path(folder).resolve(), Path(output).resolve()
    if not (folder / "index.html").is_file():
        raise RuntimeError(f"No composition at {folder / 'index.html'}; export the script first")
    # draft: 720p and lighter encoding, about twice as fast; high: full 1080p
    crf, jpeg, scale, preset = {"draft": (24, 85, 2 / 3, "veryfast"), "high": (17, 95, 1.0, "faster")}.get(quality, (17, 95, 1.0, "faster"))
    server = serve_folder(folder)
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    browsers, encoder, threads = [], None, []
    cancelled = threading.Event()
    partial = output.with_name(output.stem + ".partial.mp4")
    started = time.monotonic()
    try:
        first, info = open_composition(url, scale)
        browsers.append(first)
        width, height, duration = int(info["width"]), int(info["height"]), float(info["duration"])
        out_width, out_height = round(width * scale / 2) * 2, round(height * scale / 2) * 2
        frames = max(1, round(duration * fps))
        count = max(1, min(workers or default_workers(), frames // 30 or 1))
        for _ in range(count - 1):
            browsers.append(open_composition(url, scale)[0])
        output.parent.mkdir(parents=True, exist_ok=True)
        encoder = subprocess.Popen(
            [find_ffmpeg(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
             *(["-i", str(audio)] if audio else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]),
             "-map", "0:v", "-map", "1:a", "-shortest",
             "-vf", f"scale={out_width}:{out_height}:flags=lanczos",
             "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high",
             "-r", str(fps), "-c:a", "aac", "-b:a", "192k" if audio else "128k", "-movflags", "+faststart", str(partial)],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        # The poster is the hook's settled frame: about 1.6 s in, or earlier in a shorter first scene.
        first_scene = float(info.get("first") or 0)
        poster_frame = min(frames - 1, round((min(1.6, max(0.5, first_scene * 0.6)) if first_scene else min(1.6, duration / 2)) * fps))

        done: dict[int, bytes] = {}
        ready = threading.Condition()
        failure: list[BaseException] = []
        window = count * 8   # frames a worker may run ahead of the writer

        def work(k: int, browser: Browser) -> None:
            try:
                for i in range(k, frames, count):
                    with ready:
                        while i - written[0] > window and not failure and not cancelled.is_set():
                            ready.wait(0.5)
                        if failure or cancelled.is_set():
                            return
                    browser.evaluate(f"window.__timelines.vid.time({i / fps:.6f}, false); 0")
                    frame = browser.screenshot(width, height, jpeg)
                    with ready:
                        done[i] = frame
                        ready.notify_all()
            except BaseException as error:  # surfaced by the writer
                with ready:
                    failure.append(error)
                    ready.notify_all()

        written = [0]
        threads = [threading.Thread(target=work, args=(k, b), daemon=True) for k, b in enumerate(browsers)]
        for thread in threads:
            thread.start()
        while written[0] < frames:
            with ready:
                while written[0] not in done and not failure:
                    ready.wait(0.5)
                if failure:
                    raise failure[0]
                frame = done.pop(written[0])
            encoder.stdin.write(frame)
            if poster is not None and written[0] == poster_frame:
                poster.write_bytes(frame)
            with ready:
                written[0] += 1
                ready.notify_all()
            if progress and (written[0] % 15 == 0 or written[0] == frames):
                progress(written[0], frames)
        encoder.stdin.close()
        error = encoder.stderr.read().decode(errors="replace").strip()
        if encoder.wait() != 0:
            raise RuntimeError(f"ffmpeg failed: {error[-400:]}")
        os.replace(partial, output)
        return {"output": str(output), "frames": frames, "fps": fps, "width": out_width, "height": out_height, "workers": count,
                "duration": duration, "fonts": info.get("fonts"), "audio": bool(audio), "seconds": round(time.monotonic() - started, 1)}
    finally:
        cancelled.set()
        if encoder and encoder.poll() is None:
            encoder.kill()
            encoder.wait(timeout=5)
        if encoder:
            for stream in (encoder.stdin, encoder.stderr):
                if stream:
                    stream.close()
        active = any(thread.is_alive() for thread in threads)
        for browser in browsers:
            browser.close(force=active)
        for thread in threads:
            thread.join(timeout=5)
        partial.unlink(missing_ok=True)
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    result = render(Path(sys.argv[1]), Path(sys.argv[2]), progress=lambda d, t: print(f"\r{d}/{t}", end="", flush=True))
    print()
    print(json.dumps(result, indent=2))
