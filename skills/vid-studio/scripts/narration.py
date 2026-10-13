"""Text to speech for video scripts: one voiceover clip per beat, from a provider the channel picks.

Standard library only. Every provider returns 16-bit PCM WAV, so timing, trimming and joining need no
extra tools; ffmpeg only mixes the final track at render time.

Providers:
  system      the computer's own voice (macOS `say`, Linux `espeak-ng`), offline and free; for drafts
  piper       Piper neural voices, offline and free (`pip install piper-tts`); downloads a voice once
  elevenlabs  ElevenLabs (API key); returns word timings, so captions land on the exact word
  sarvam      Sarvam AI Bulbul (API key); Indian voices for Hindi, Hinglish and Indian English
  openai      OpenAI speech (API key); takes speaking instructions from the channel's persona
  google      Google Cloud Text-to-Speech (API key); Hindi and Indian English neural voices

Keys come from the environment (ELEVENLABS_API_KEY, …) or from <studio>/.secrets.json, which the UI writes
and never reads back.
"""

from __future__ import annotations

import array
import base64
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

USER_AGENT = "vid-studio/1.0"
SECRETS_FILE = ".secrets.json"
DEFAULT_NARRATION = {"provider": "", "voice": "", "model": "", "speed": 1.0, "style": "", "lexicon": {}, "pause": 0.3}
TAIL = 0.3  # seconds of air after a beat's last word, unless the channel sets its own pause
SAMPLE_TEXT = {
    "English": "Your electricity bill went up last month. Here's what changed, and what you can still do about it.",
    "Hindi": "पिछले महीने आपका बिजली का बिल बढ़ गया. जानिए क्या बदला, और अब भी आप क्या कर सकते हैं.",
    "Hinglish": "पिछले महीने आपका electricity bill बढ़ गया. जानिए क्या बदला, और अब भी आप क्या कर सकते हैं.",
}


class TTSError(RuntimeError):
    """A provider could not speak: missing key or tool, a rejected request, or bad audio."""


# ---------------------------------------------------------------- secrets: env first, then <root>/.secrets.json

def secrets_path(root: Path) -> Path:
    return Path(root) / SECRETS_FILE


def read_secrets(root: Path) -> dict:
    path = secrets_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def secret(root: Path, name: str) -> str:
    return (os.environ.get(name) or str(read_secrets(root).get(name) or "")).strip()


def set_secret(root: Path, name: str, value: str | None) -> None:
    """Save (or with an empty value, remove) one secret. The file is readable by this user only."""
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", name or ""):
        raise ValueError(f"Invalid secret name: {name!r}")
    data = read_secrets(root)
    value = (value or "").strip()
    if value:
        if len(value) > 8000 or any(ch in value for ch in "\r\n\0"):
            raise ValueError("That doesn't look like a key")
        data[name] = value
    else:
        data.pop(name, None)
    path = secrets_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


# ---------------------------------------------------------------- WAV: 16-bit PCM in, mono 16-bit PCM out

class Audio:
    """Mono 16-bit PCM samples at a sample rate, plus optional word timings [(word, start, end)]."""

    def __init__(self, samples: array.array, rate: int, words: list | None = None):
        self.samples, self.rate, self.words = samples, rate, words

    @property
    def duration(self) -> float:
        return len(self.samples) / self.rate if self.rate else 0.0

    def wav(self) -> bytes:
        out = io.BytesIO()
        with wave.open(out, "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(self.rate)
            data = array.array("h", self.samples)
            if sys.byteorder == "big":
                data.byteswap()
            handle.writeframes(data.tobytes())
        return out.getvalue()


def _fix_sizes(data: bytes) -> bytes:
    """Streamed WAVs (espeak/piper to stdout) carry 0 or 0xFFFFFFFF sizes; rewrite them from the real length."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return data
    out, at = bytearray(data), 12
    out[4:8] = (len(data) - 8).to_bytes(4, "little")
    while at + 8 <= len(out):
        chunk, size = bytes(out[at:at + 4]), int.from_bytes(out[at + 4:at + 8], "little")
        if chunk == b"data":
            out[at + 4:at + 8] = (len(out) - at - 8).to_bytes(4, "little")
            break
        at += 8 + size + (size & 1)
    return bytes(out)


def read_wav(data: bytes) -> Audio:
    try:
        with wave.open(io.BytesIO(_fix_sizes(data)), "rb") as handle:
            channels, width, rate = handle.getnchannels(), handle.getsampwidth(), handle.getframerate()
            frames = handle.readframes(handle.getnframes())
    except (wave.Error, EOFError) as error:
        raise TTSError(f"The provider returned audio that isn't a 16-bit WAV ({error})")
    if width != 2:
        raise TTSError(f"Expected 16-bit audio, got {width * 8}-bit")
    samples = array.array("h")
    samples.frombytes(frames[: len(frames) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    if channels > 1:
        samples = array.array("h", (int(sum(samples[i:i + channels]) / channels) for i in range(0, len(samples), channels)))
    return Audio(samples, rate)


def pcm_audio(data: bytes, rate: int) -> Audio:
    samples = array.array("h")
    samples.frombytes(data[: len(data) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    return Audio(samples, rate)


def join(parts: list[Audio], gap: float = 0.12) -> Audio:
    """Concatenate clips of one rate, with a short pause between them, shifting word timings along."""
    if not parts:
        return Audio(array.array("h"), 24000)
    rate = parts[0].rate
    if any(p.rate != rate for p in parts):
        raise TTSError("The provider returned clips at different sample rates")
    samples, words, offset = array.array("h"), [], 0.0
    silence = array.array("h", bytes(2 * int(rate * gap)))
    for i, part in enumerate(parts):
        if i:
            samples.extend(silence)
            offset += gap
        if part.words is not None and words is not None:
            words.extend((w, s + offset, e + offset) for w, s, e in part.words)
        else:
            words = None
        samples.extend(part.samples)
        offset += part.duration
    return Audio(samples, rate, words)


def trim(audio: Audio, threshold: int = 500, keep_head: float = 0.05, keep_tail: float = 0.08) -> Audio:
    """Cut leading and trailing silence (most engines pad both ends), keeping a breath of air."""
    samples, rate = audio.samples, audio.rate
    window = max(1, rate // 100)  # 10 ms
    loud = [i for i in range(0, len(samples), window) if max(map(abs, samples[i:i + window]), default=0) > threshold]
    if not loud:
        return audio
    start = max(0, loud[0] - int(rate * keep_head))
    end = min(len(samples), loud[-1] + window + int(rate * keep_tail))
    shift = start / rate
    words = None if audio.words is None else [(w, max(0.0, s - shift), max(0.0, e - shift)) for w, s, e in audio.words]
    return Audio(samples[start:end], rate, words)


def words_from_characters(characters: list, starts: list, ends: list) -> list:
    """Group per-character timings (ElevenLabs alignment) into [(word, start, end)]."""
    words, current, first, last = [], "", None, None
    for char, start, end in zip(characters, starts, ends):
        if char.isspace():
            if current:
                words.append((current, first, last))
            current, first = "", None
            continue
        if first is None:
            first = float(start)
        current += char
        last = float(end)
    if current:
        words.append((current, first, last))
    return words


def split_text(text: str, limit: int) -> list[str]:
    """Split at sentence ends (then commas, then spaces) so each request stays under a provider's limit."""
    text = text.strip()
    if len(text) <= limit:
        return [text] if text else []
    pieces, current = [], ""
    for sentence in re.split(r"(?<=[.!?।])\s+", text):
        while len(sentence) > limit:
            cut = max(sentence.rfind(", ", 0, limit), sentence.rfind(" ", 0, limit))
            cut = cut if cut > 0 else limit
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + 1 + len(sentence) > limit:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return [p for p in pieces if p]


# ---------------------------------------------------------------- HTTP

def http(method: str, url: str, headers: dict | None = None, body=None, timeout: int = 120) -> tuple[bytes, str]:
    """One request; returns (body, content type). Raises TTSError with the provider's own message on failure."""
    data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    request = urllib.request.Request(url, data=data, method=method, headers={
        "User-Agent": USER_AGENT, **({"Content-Type": "application/json"} if isinstance(body, (dict, list)) else {}), **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        detail = error.read()[:2000].decode("utf-8", "replace")
        try:
            parsed = json.loads(detail)
            found = parsed.get("detail") or parsed.get("error") or parsed.get("message") or parsed
            if isinstance(found, dict):
                found = found.get("message") or found.get("status") or json.dumps(found)
            detail = str(found)
        except (json.JSONDecodeError, AttributeError):
            pass
        hint = " (check the API key)" if error.code in (401, 403) else " (rate limit or quota)" if error.code == 429 else ""
        raise TTSError(f"{urllib.parse.urlsplit(url).hostname} said HTTP {error.code}{hint}: {detail[:300]}")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise TTSError(f"Couldn't reach {urllib.parse.urlsplit(url).hostname}: {getattr(error, 'reason', error)}")


def http_json(method: str, url: str, headers: dict | None = None, body=None, timeout: int = 120):
    data, _ = http(method, url, headers, body, timeout)
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        raise TTSError(f"{urllib.parse.urlsplit(url).hostname} returned something that isn't JSON")


# ---------------------------------------------------------------- providers

def lang_family(language: str) -> str:
    """English, Hindi or Hinglish (or a BCP-47 code) → "en" or "hi"."""
    low = (language or "").casefold()
    return "hi" if low.startswith(("hi", "hinglish")) or low in ("hindi",) else "en"


class Provider:
    id = ""
    name = ""
    kind = "cloud"           # "local" runs on this computer; "cloud" sends the text to a service
    key = ""                 # environment/secrets name of the API key
    key_url = ""             # where to get one
    models: list = []        # [(id, label)]
    word_timings = False     # whether captions can follow the exact word
    note = ""

    def problem(self, root: Path) -> str:
        """Why this provider can't speak right now, or an empty string."""
        return f"Add your {self.name} API key" if self.key and not secret(root, self.key) else ""

    def voices(self, root: Path, language: str) -> list[dict]:
        return []

    def default_voice(self, language: str) -> str:
        return ""

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        raise NotImplementedError

    def describe(self, root: Path) -> dict:
        return {"id": self.id, "name": self.name, "kind": self.kind, "ready": not self.problem(root), "problem": self.problem(root),
                "needs_key": bool(self.key), "key_name": self.key, "key_set": bool(self.key and secret(root, self.key)),
                "key_from_env": bool(self.key and os.environ.get(self.key)), "key_url": self.key_url,
                "models": [{"id": m, "label": label} for m, label in self.models], "word_timings": self.word_timings, "note": self.note}


def _run(command: list[str], text: str | None = None, timeout: int = 180) -> bytes:
    try:
        done = subprocess.run(command, input=text.encode() if text is not None else None, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        raise TTSError(f"{command[0]} is not installed")
    except subprocess.TimeoutExpired:
        raise TTSError(f"{Path(command[0]).name} took longer than {timeout}s")
    if done.returncode:
        raise TTSError(f"{Path(command[0]).name} failed: {done.stderr.decode(errors='replace').strip()[-300:]}")
    return done.stdout


class SystemProvider(Provider):
    id, name, kind = "system", "System voice", "local"
    note = "Built into the computer and robotic. Good for checking timing before you pay for a real voice."

    def tool(self) -> tuple[str, str] | None:
        if sys.platform == "darwin" and shutil.which("say"):
            return "say", shutil.which("say")
        for name in ("espeak-ng", "espeak"):
            if shutil.which(name):
                return "espeak", shutil.which(name)
        return None

    def problem(self, root: Path) -> str:
        return "" if self.tool() else ("Install espeak-ng (Ubuntu: `sudo apt install espeak-ng`; macOS has `say` built in)")

    def voices(self, root: Path, language: str) -> list[dict]:
        tool = self.tool()
        if not tool:
            return []
        family, listed = lang_family(language), []
        if tool[0] == "say":
            for line in _run([tool[1], "-v", "?"]).decode(errors="replace").splitlines():
                match = re.match(r"^(.+?)\s{2,}([a-z]{2}[_-][A-Z]{2})\s", line)
                if match and match[2].lower().startswith(family):
                    listed.append({"id": match[1].strip(), "name": match[1].strip(), "language": match[2]})
            return listed
        for line in _run([tool[1], f"--voices={family}"]).decode(errors="replace").splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                listed.append({"id": parts[4] if parts[4].startswith("mb/") else parts[1], "name": parts[3].replace("_", " "),
                               "language": parts[1], "gender": {"M": "male", "F": "female"}.get(parts[2][-1:], "")})
        return [v for v in listed if not v["id"].startswith("mb/")] or listed

    def default_voice(self, language: str) -> str:
        if sys.platform == "darwin":
            return "Lekha" if lang_family(language) == "hi" else "Samantha"
        return "hi" if lang_family(language) == "hi" else "en-us"

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        tool = self.tool()
        if not tool:
            raise TTSError(self.problem(root))
        voice = settings.get("voice") or self.default_voice(language)
        with tempfile.TemporaryDirectory(prefix="vid-tts-") as tmp:
            out = Path(tmp) / "out.wav"
            if tool[0] == "say":
                _run([tool[1], "-v", voice, "-r", str(round(175 * settings.get("speed", 1.0))),
                      "--file-format=WAVE", "--data-format=LEI16@22050", "-o", str(out), "-f", "-"], text)
            else:
                _run([tool[1], "-v", voice, "-s", str(round(165 * settings.get("speed", 1.0))), "-w", str(out), "--stdin"], text)
            return read_wav(out.read_bytes())


PIPER_VOICES = [
    # (id, language, name, gender)
    ("en_US-lessac-medium", "en_US", "Lessac (US)", "female"), ("en_US-ryan-high", "en_US", "Ryan (US)", "male"),
    ("en_US-amy-medium", "en_US", "Amy (US)", "female"), ("en_US-joe-medium", "en_US", "Joe (US)", "male"),
    ("en_GB-alba-medium", "en_GB", "Alba (UK)", "female"), ("en_GB-northern_english_male-medium", "en_GB", "Northern English (UK)", "male"),
    ("hi_IN-pratham-medium", "hi_IN", "Pratham (Hindi)", "male"), ("hi_IN-priyamvada-medium", "hi_IN", "Priyamvada (Hindi)", "female"),
    ("hi_IN-rohan-medium", "hi_IN", "Rohan (Hindi)", "male"),
]
PIPER_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/{family}/{code}/{name}/{quality}/{voice}{ext}?download=true"


class PiperProvider(Provider):
    id, name, kind = "piper", "Piper", "local"
    note = "Natural offline voices that run on your computer, free. Each voice downloads once (about 60 MB)."

    def command(self) -> list[str] | None:
        if os.environ.get("VID_STUDIO_PIPER"):
            return [os.environ["VID_STUDIO_PIPER"]]
        if shutil.which("piper"):
            return [shutil.which("piper")]
        try:
            import importlib.util
            if importlib.util.find_spec("piper") is not None:
                return [sys.executable, "-m", "piper"]
        except (ImportError, ValueError):
            pass
        return None

    def problem(self, root: Path) -> str:
        return "" if self.command() else "Install Piper: `pip install piper-tts`"

    def voices(self, root: Path, language: str) -> list[dict]:
        family = lang_family(language)
        return [{"id": v, "name": name, "language": code, "gender": gender, "downloaded": self.model(root, v).is_file()}
                for v, code, name, gender in PIPER_VOICES if code.startswith(family)]

    def default_voice(self, language: str) -> str:
        return "hi_IN-priyamvada-medium" if lang_family(language) == "hi" else "en_US-lessac-medium"

    def model(self, root: Path, voice: str) -> Path:
        if voice.endswith(".onnx") and Path(voice).expanduser().is_absolute():
            return Path(voice).expanduser()
        return Path(root) / ".cache" / "piper" / f"{voice}.onnx"

    def download(self, root: Path, voice: str) -> Path:
        model = self.model(root, voice)
        if model.is_file() and model.with_suffix(".onnx.json").is_file():
            return model
        match = re.fullmatch(r"([a-z]{2})_([A-Z]{2})-([\w]+)-(x_low|low|medium|high)", voice)
        if not match:
            raise TTSError(f"Unknown Piper voice {voice!r}; use an id like en_US-lessac-medium or a path to a .onnx model")
        model.parent.mkdir(parents=True, exist_ok=True)
        for ext in (".onnx.json", ".onnx"):
            url = PIPER_URL.format(family=match[1], code=f"{match[1]}_{match[2]}", name=match[3], quality=match[4], voice=voice, ext=ext)
            data, _ = http("GET", url, timeout=600)
            target = model.parent / f"{voice}{ext}"
            target.with_suffix(target.suffix + ".part").write_bytes(data)
            target.with_suffix(target.suffix + ".part").replace(target)
        return model

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        command = self.command()
        if not command:
            raise TTSError(self.problem(root))
        model = self.download(root, settings.get("voice") or self.default_voice(language))
        with tempfile.TemporaryDirectory(prefix="vid-tts-") as tmp:
            out = Path(tmp) / "out.wav"
            _run(command + ["-m", str(model), "-f", str(out), "--length-scale", f"{1 / max(0.5, settings.get('speed', 1.0)):.3f}"], text)
            return read_wav(out.read_bytes())


class ElevenLabsProvider(Provider):
    id, name, key = "elevenlabs", "ElevenLabs", "ELEVENLABS_API_KEY"
    key_url = "https://elevenlabs.io/app/settings/api-keys"
    models = [("eleven_multilingual_v2", "Multilingual v2 (best quality, Hindi and English)"),
              ("eleven_v3", "v3 (most expressive)"), ("eleven_flash_v2_5", "Flash v2.5 (fast, cheaper)")]
    word_timings = True
    note = "Very natural voices in Hindi and English, including your own cloned voice. Captions follow the exact words."
    BASE = "https://api.elevenlabs.io/v1"

    def voices(self, root: Path, language: str) -> list[dict]:
        data = http_json("GET", f"{self.BASE}/voices", {"xi-api-key": secret(root, self.key)})
        listed = []
        for voice in data.get("voices", []):
            labels = voice.get("labels") or {}
            listed.append({"id": voice.get("voice_id"), "name": voice.get("name"), "gender": labels.get("gender", ""),
                           "language": labels.get("language") or labels.get("accent", ""), "category": voice.get("category", ""),
                           "preview": voice.get("preview_url", "")})
        return listed

    def default_voice(self, language: str) -> str:
        return "JBFqnCBsd6RMkjVDRZzb"  # "George", a premade voice every account has

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        voice = settings.get("voice") or self.default_voice(language)
        body = {"text": text, "model_id": settings.get("model") or self.models[0][0],
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True,
                                   "speed": max(0.7, min(1.2, settings.get("speed", 1.0)))}}
        url = f"{self.BASE}/text-to-speech/{urllib.parse.quote(voice)}/with-timestamps?output_format=pcm_24000"
        data = http_json("POST", url, {"xi-api-key": secret(root, self.key)}, body)
        try:
            audio = pcm_audio(base64.b64decode(data["audio_base64"]), 24000)
        except (KeyError, ValueError, TypeError):
            raise TTSError("ElevenLabs returned no audio")
        alignment = data.get("alignment") or data.get("normalized_alignment") or {}
        if alignment.get("characters"):
            audio.words = words_from_characters(alignment["characters"], alignment.get("character_start_times_seconds", []),
                                                alignment.get("character_end_times_seconds", []))
        return audio


SARVAM_SPEAKERS = [("anushka", "female"), ("manisha", "female"), ("vidya", "female"), ("arya", "female"),
                   ("abhilash", "male"), ("karun", "male"), ("hitesh", "male")]


class SarvamProvider(Provider):
    id, name, key = "sarvam", "Sarvam AI", "SARVAM_API_KEY"
    key_url = "https://dashboard.sarvam.ai"
    models = [("bulbul:v2", "Bulbul v2")]
    note = "Indian voices made for Hindi, Hinglish and Indian English; numbers and code-mixed text read naturally."
    URL = "https://api.sarvam.ai/text-to-speech"
    LIMIT = 1500

    def voices(self, root: Path, language: str) -> list[dict]:
        return [{"id": s, "name": s.title(), "gender": g, "language": self.language_code(language)} for s, g in SARVAM_SPEAKERS]

    def default_voice(self, language: str) -> str:
        return "anushka"

    def language_code(self, language: str) -> str:
        if re.fullmatch(r"[a-z]{2}-IN", language or ""):
            return language
        return "hi-IN" if lang_family(language) == "hi" else "en-IN"

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        parts = []
        for piece in split_text(text, self.LIMIT):
            body = {"text": piece, "target_language_code": self.language_code(language),
                    "speaker": settings.get("voice") or self.default_voice(language), "model": settings.get("model") or self.models[0][0],
                    "pace": max(0.5, min(2.0, settings.get("speed", 1.0))), "speech_sample_rate": 24000, "enable_preprocessing": True}
            data = http_json("POST", self.URL, {"api-subscription-key": secret(root, self.key)}, body)
            audios = data.get("audios") or []
            if not audios:
                raise TTSError("Sarvam returned no audio")
            parts.append(join([read_wav(base64.b64decode(a)) for a in audios], 0))
        return join(parts)


OPENAI_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]


class OpenAIProvider(Provider):
    id, name, key = "openai", "OpenAI", "OPENAI_API_KEY"
    key_url = "https://platform.openai.com/api-keys"
    models = [("gpt-4o-mini-tts", "gpt-4o-mini-tts (follows speaking instructions)"), ("tts-1-hd", "tts-1-hd"), ("tts-1", "tts-1 (fast)")]
    note = "Follows how-to-speak instructions, taken from the channel's style line."
    URL = "https://api.openai.com/v1/audio/speech"
    LIMIT = 4000

    def voices(self, root: Path, language: str) -> list[dict]:
        return [{"id": v, "name": v.title()} for v in OPENAI_VOICES]

    def default_voice(self, language: str) -> str:
        return "coral"

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        model, parts = settings.get("model") or self.models[0][0], []
        for piece in split_text(text, self.LIMIT):
            body = {"model": model, "voice": settings.get("voice") or self.default_voice(language), "input": piece,
                    "response_format": "pcm", "speed": max(0.25, min(4.0, settings.get("speed", 1.0)))}
            if settings.get("style") and model.startswith("gpt-"):
                body["instructions"] = settings["style"]
            data, _ = http("POST", self.URL, {"Authorization": f"Bearer {secret(root, self.key)}"}, body)
            parts.append(pcm_audio(data, 24000))  # pcm: 24 kHz, 16-bit, mono
        return join(parts)


class GoogleProvider(Provider):
    id, name, key = "google", "Google Cloud", "GOOGLE_TTS_API_KEY"
    key_url = "https://console.cloud.google.com/apis/library/texttospeech.googleapis.com"
    note = "Chirp 3 HD and Neural2 voices for Hindi and Indian English. Needs an API key with Text-to-Speech enabled."
    BASE = "https://texttospeech.googleapis.com/v1"
    LIMIT = 4500

    def language_code(self, language: str) -> str:
        if re.fullmatch(r"[a-z]{2,3}-[A-Z]{2}", language or ""):
            return language
        return "hi-IN" if lang_family(language) == "hi" else "en-IN"

    def voices(self, root: Path, language: str) -> list[dict]:
        code = self.language_code(language)
        data = http_json("GET", f"{self.BASE}/voices?" + urllib.parse.urlencode({"languageCode": code, "key": secret(root, self.key)}))
        rank = lambda v: (0 if "Chirp3-HD" in v["name"] else 1 if "Neural2" in v["name"] else 2 if "Wavenet" in v["name"] else 3, v["name"])
        return [{"id": v["name"], "name": v["name"], "language": code, "gender": str(v.get("ssmlGender", "")).lower()}
                for v in sorted(data.get("voices", []), key=rank)]

    def default_voice(self, language: str) -> str:
        return "hi-IN-Chirp3-HD-Kore" if lang_family(language) == "hi" else "en-IN-Chirp3-HD-Kore"

    def synthesize(self, root: Path, text: str, settings: dict, language: str) -> Audio:
        voice = settings.get("voice") or self.default_voice(language)
        code = "-".join(voice.split("-")[:2]) if re.match(r"^[a-z]{2,3}-[A-Z]{2}-", voice) else self.language_code(language)
        parts = []
        for piece in split_text(text, self.LIMIT):
            body = {"input": {"text": piece}, "voice": {"languageCode": code, "name": voice},
                    "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000, "speakingRate": max(0.25, min(4.0, settings.get("speed", 1.0)))}}
            data = http_json("POST", f"{self.BASE}/text:synthesize?key={urllib.parse.quote(secret(root, self.key))}", None, body)
            if not data.get("audioContent"):
                raise TTSError("Google returned no audio")
            parts.append(read_wav(base64.b64decode(data["audioContent"])))  # LINEAR16 comes with a WAV header
        return join(parts)


PROVIDERS: dict[str, Provider] = {p.id: p for p in (SystemProvider(), PiperProvider(), ElevenLabsProvider(), SarvamProvider(),
                                                    OpenAIProvider(), GoogleProvider())}


def provider(provider_id: str) -> Provider:
    if provider_id not in PROVIDERS:
        raise KeyError(f"Unknown voice provider {provider_id!r}. Providers: {', '.join(PROVIDERS)}")
    return PROVIDERS[provider_id]


def providers(root: Path) -> list[dict]:
    return [p.describe(root) for p in PROVIDERS.values()]


# ---------------------------------------------------------------- settings and synthesis

def clean_settings(settings: dict) -> dict:
    """Validate a channel's narration settings (the provider may be "" for no voiceover)."""
    if not isinstance(settings, dict):
        raise ValueError("narration must be a JSON object")
    unknown = set(settings) - set(DEFAULT_NARRATION)
    if unknown:
        raise ValueError(f"Unknown narration key: {', '.join(sorted(unknown))}. Allowed: {', '.join(sorted(DEFAULT_NARRATION))}")
    result = json.loads(json.dumps(DEFAULT_NARRATION)) | settings
    if result["provider"] and result["provider"] not in PROVIDERS:
        raise ValueError(f"narration.provider must be one of: {', '.join(PROVIDERS)} (or empty for no voiceover)")
    for key in ("voice", "model", "style"):
        if not isinstance(result[key], str) or len(result[key]) > (2000 if key == "style" else 300):
            raise ValueError(f"narration.{key} must be text")
        result[key] = result[key].strip()
    if result["model"] and result["provider"] and PROVIDERS[result["provider"]].models \
            and result["model"] not in {m for m, _ in PROVIDERS[result["provider"]].models}:
        raise ValueError(f"narration.model for {result['provider']} must be one of: {', '.join(m for m, _ in PROVIDERS[result['provider']].models)}")
    for key, low, high in (("speed", 0.7, 1.3), ("pause", 0.0, 1.5)):
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"narration.{key} must be a number from {low} to {high}")
    lexicon = result["lexicon"]
    if not isinstance(lexicon, dict) or len(lexicon) > 300 or not all(
            isinstance(k, str) and isinstance(v, str) and k.strip() and len(k) <= 100 and len(v) <= 200 for k, v in lexicon.items()):
        raise ValueError("narration.lexicon must map up to 300 words to how they are said, e.g. {\"UPI\": \"U P I\"}")
    result["lexicon"] = {k.strip(): v.strip() for k, v in lexicon.items()}
    return result


def apply_lexicon(text: str, lexicon: dict) -> str:
    """Swap whole words for how they should be said (longest first, so "UPI Lite" beats "UPI")."""
    for word in sorted(lexicon, key=len, reverse=True):
        text = re.sub(rf"(?<![\w]){re.escape(word)}(?![\w])", lexicon[word], text)
    return text


def settings_key(settings: dict, language: str) -> str:
    """Changes whenever the same text would come out sounding different."""
    relevant = {k: settings.get(k) for k in ("provider", "voice", "model", "speed", "style", "lexicon")}
    return hashlib.sha1(json.dumps([relevant, language], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def clip_key(settings: dict, language: str, text: str) -> str:
    return hashlib.sha1(f"{settings_key(settings, language)}\n{text}".encode()).hexdigest()[:12]


def speak(root: Path, text: str, settings: dict, language: str) -> Audio:
    """Synthesize one clip with the channel's settings: lexicon applied, silence trimmed."""
    if not settings.get("provider"):
        raise TTSError("Choose a voice provider for this channel first")
    chosen = provider(settings["provider"])
    problem = chosen.problem(root)
    if problem:
        raise TTSError(problem)
    spoken = apply_lexicon(text, settings.get("lexicon") or {})
    audio = chosen.synthesize(root, spoken, settings, language)
    if not len(audio.samples):
        raise TTSError(f"{chosen.name} returned silence")
    return trim(audio)


def word_times(audio: Audio, text: str) -> list | None:
    """Timings for each word of the caption text, when the provider's words line up with it."""
    if audio.words is None:
        return None
    shown = text.split()
    if len(shown) != len(audio.words):
        return None
    return [[round(s, 3), round(max(e, s + 0.01), 3)] for _, s, e in audio.words]


def srt(cues: list[tuple[float, float, str]]) -> str:
    """SubRip text from (start, end, text) cues; for YouTube captions and editors."""
    stamp = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}"
    return "".join(f"{i}\n{stamp(s)} --> {stamp(e)}\n{text}\n\n" for i, (s, e, text) in enumerate(cues, 1))
