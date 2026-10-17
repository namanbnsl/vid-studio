"""Text to speech: providers (with their HTTP calls faked), audio handling, and the studio's voiceover."""
import array
import base64
import contextlib
import http.client
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
import wave
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "vid-studio" / "scripts"))
import narration as tts  # noqa: E402
import render  # noqa: E402
import studio  # noqa: E402
from support import idea_script  # noqa: E402


def tone(seconds: float, rate: int = 24000, lead: float = 0.0, tail: float = 0.0, channels: int = 1) -> bytes:
    """A WAV: silence, a loud square wave, silence."""
    samples = [0] * int(rate * lead) + [6000 if i // 40 % 2 else -6000 for i in range(int(rate * seconds))] + [0] * int(rate * tail)
    out = io.BytesIO()
    with wave.open(out, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(array.array("h", [s for s in samples for _ in range(channels)]).tobytes())
    return out.getvalue()


class FakeProvider(tts.Provider):
    """Speaks 0.1 s per word, so lengths are predictable, and records what it was asked to say."""
    id, name, kind = "fake", "Fake", "local"
    word_timings = True

    def __init__(self):
        self.calls = []

    def synthesize(self, root, text, settings, language):
        self.calls.append((text, settings.get("voice"), language))
        words = text.split()
        audio = tts.read_wav(tone(0.1 * len(words)))
        audio.words = [(w, i * 0.1, i * 0.1 + 0.09) for i, w in enumerate(words)]
        return audio


class AudioTest(unittest.TestCase):
    def test_streamed_and_stereo_wavs_are_read(self):
        data = bytearray(tone(0.5, 22050, channels=2))
        data[4:8] = b"\xff\xff\xff\xff"  # espeak and piper write placeholder sizes when streaming
        data[40:44] = b"\xff\xff\xff\xff"
        audio = tts.read_wav(bytes(data))
        self.assertEqual(audio.rate, 22050)
        self.assertAlmostEqual(audio.duration, 0.5, places=2)
        self.assertEqual(tts.read_wav(audio.wav()).duration, audio.duration)
        with self.assertRaises(tts.TTSError):
            tts.read_wav(b"not audio")

    def test_trim_join_and_word_timings(self):
        audio = tts.read_wav(tone(1.0, lead=0.5, tail=0.7))
        audio.words = [("a", 0.6, 0.9), ("b", 1.0, 1.4)]
        trimmed = tts.trim(audio)
        self.assertAlmostEqual(trimmed.duration, 1.0 + 0.05 + 0.08, delta=0.03)
        self.assertAlmostEqual(trimmed.words[0][1], 0.15, delta=0.02)
        joined = tts.join([trimmed, trimmed], gap=0.2)
        self.assertAlmostEqual(joined.duration, trimmed.duration * 2 + 0.2, places=3)
        self.assertAlmostEqual(joined.words[2][1], trimmed.duration + 0.2 + trimmed.words[0][1], places=3)
        self.assertIsNone(tts.join([trimmed, tts.read_wav(tone(0.2))]).words)  # one clip without timings drops them all
        with self.assertRaises(tts.TTSError):
            tts.join([trimmed, tts.read_wav(tone(0.2, 16000))])
        self.assertEqual(tts.words_from_characters(list("Hi  you."), [0, .1, .2, .3, .4, .5, .6, .7], [.1, .2, .3, .4, .5, .6, .7, .8]),
                         [("Hi", 0.0, 0.2), ("you.", 0.4, 0.8)])

    def test_text_is_split_under_a_limit_at_sentence_ends(self):
        text = "One two three. Four five six! " + "word " * 30
        pieces = tts.split_text(text, 40)
        self.assertTrue(all(len(p) <= 40 for p in pieces))
        self.assertEqual(pieces[0], "One two three. Four five six!")
        self.assertEqual(" ".join(pieces).split(), text.split())
        self.assertEqual(tts.split_text("  ", 10), [])

    def test_lexicon_settings_and_srt(self):
        self.assertEqual(tts.apply_lexicon("UPI Lite beats UPI, not UPIs", {"UPI": "U P I", "UPI Lite": "U P I lite"}),
                         "U P I lite beats U P I, not UPIs")
        self.assertEqual(tts.clean_settings({"provider": "sarvam", "lexicon": {" UPI ": "U P I"}})["lexicon"], {"UPI": "U P I"})
        for bad in ({"provider": "nope"}, {"speed": 3}, {"pause": True}, {"lexicon": ["x"]}, {"colour": 1},
                    {"provider": "elevenlabs", "model": "gpt-4o-mini-tts"}):
            with self.assertRaises(ValueError, msg=bad):
                tts.clean_settings(bad)
        a = {"provider": "sarvam", "voice": "anushka", "speed": 1.0}
        self.assertEqual(tts.settings_key(a, "Hindi"), tts.settings_key(dict(a, pause=1.0), "Hindi"))  # pause doesn't change the sound
        self.assertNotEqual(tts.settings_key(a, "Hindi"), tts.settings_key(dict(a, speed=1.1), "Hindi"))
        self.assertEqual(tts.srt([(0, 1.25, "Hi"), (61.5, 3725.01, "there")]),
                         "1\n00:00:00,000 --> 00:00:01,250\nHi\n\n2\n00:01:01,500 --> 01:02:05,010\nthere\n\n")


class SecretsTest(unittest.TestCase):
    def test_keys_are_private_and_the_environment_wins(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SARVAM_API_KEY", None)
            root = Path(tmp)
            self.assertEqual(tts.secret(root, "SARVAM_API_KEY"), "")
            tts.set_secret(root, "SARVAM_API_KEY", " sk-123 ")
            self.assertEqual(tts.secret(root, "SARVAM_API_KEY"), "sk-123")
            self.assertEqual(stat.S_IMODE(tts.secrets_path(root).stat().st_mode), 0o600)
            os.environ["SARVAM_API_KEY"] = "from-env"
            self.assertEqual(tts.secret(root, "SARVAM_API_KEY"), "from-env")
            del os.environ["SARVAM_API_KEY"]
            tts.set_secret(root, "SARVAM_API_KEY", "")
            self.assertEqual(tts.read_secrets(root), {})
            for name, value in (("lower", "x"), ("SARVAM_API_KEY", "a\nb")):
                with self.assertRaises(ValueError):
                    tts.set_secret(root, name, value)


class ProviderTest(unittest.TestCase):
    """Each cloud provider sends what its API documents and turns the reply into audio."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ("ELEVENLABS_API_KEY", "SARVAM_API_KEY", "OPENAI_API_KEY", "GOOGLE_TTS_API_KEY"):
            tts.set_secret(self.root, name, f"key-{name}")
        self.env = mock.patch.dict(os.environ, {k: "" for k in ("ELEVENLABS_API_KEY", "SARVAM_API_KEY", "OPENAI_API_KEY", "GOOGLE_TTS_API_KEY")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def fake_http(self, reply):
        calls = []

        def http(method, url, headers=None, body=None, timeout=120):
            calls.append({"method": method, "url": url, "headers": headers or {}, "body": body})
            data = reply(calls[-1])
            return (data if isinstance(data, bytes) else json.dumps(data).encode()), "application/json"
        return calls, mock.patch.object(tts, "http", http)

    def test_elevenlabs_returns_word_timings(self):
        pcm = tts.read_wav(tone(0.4, lead=0.2)).samples.tobytes()
        text = "Bill up"
        chars = list(text)
        reply = {"audio_base64": base64.b64encode(pcm).decode(),
                 "alignment": {"characters": chars, "character_start_times_seconds": [0.2 + 0.05 * i for i in range(len(chars))],
                               "character_end_times_seconds": [0.25 + 0.05 * i for i in range(len(chars))]}}
        calls, patch = self.fake_http(lambda call: reply)
        with patch:
            audio = tts.speak(self.root, text, {"provider": "elevenlabs", "voice": "v1", "speed": 1.0}, "Hindi")
        call = calls[0]
        self.assertEqual(call["url"], "https://api.elevenlabs.io/v1/text-to-speech/v1/with-timestamps?output_format=pcm_24000")
        self.assertEqual(call["headers"], {"xi-api-key": "key-ELEVENLABS_API_KEY"})
        self.assertEqual((call["body"]["text"], call["body"]["model_id"]), (text, "eleven_multilingual_v2"))
        self.assertEqual([w for w, _, _ in audio.words], ["Bill", "up"])
        self.assertAlmostEqual(audio.words[0][1], 0.05, delta=0.02)  # shifted by the trimmed lead-in
        self.assertEqual(tts.word_times(audio, "Bill up!")[0][0], round(audio.words[0][1], 3))
        self.assertIsNone(tts.word_times(audio, "Bill went up"))

    def test_sarvam_speaks_hinglish_as_hindi_in_chunks(self):
        wav = base64.b64encode(tone(0.3)).decode()
        calls, patch = self.fake_http(lambda call: {"request_id": "r", "audios": [wav]})
        long = ("यह एक लंबा वाक्य है. " * 120).strip()
        with patch:
            audio = tts.speak(self.root, long, {"provider": "sarvam", "voice": "", "speed": 1.1, "lexicon": {"वाक्य": "line"}}, "Hinglish")
        self.assertGreater(len(calls), 1)
        body = calls[0]["body"]
        self.assertEqual(calls[0]["url"], "https://api.sarvam.ai/text-to-speech")
        self.assertEqual(calls[0]["headers"], {"api-subscription-key": "key-SARVAM_API_KEY"})
        self.assertEqual((body["target_language_code"], body["speaker"], body["model"], body["pace"]), ("hi-IN", "anushka", "bulbul:v2", 1.1))
        self.assertTrue(all(len(c["body"]["text"]) <= tts.SarvamProvider.LIMIT for c in calls))
        self.assertIn("line", body["text"])
        self.assertGreater(audio.duration, 0.3 * len(calls))

    def test_openai_reads_in_the_channel_persona(self):
        pcm = tts.read_wav(tone(0.5)).samples.tobytes()
        calls, patch = self.fake_http(lambda call: pcm)
        with patch:
            audio = tts.speak(self.root, "Hello there.", {"provider": "openai", "style": "A calm older sister", "speed": 1.0}, "English")
        body = calls[0]["body"]
        self.assertEqual(calls[0]["headers"], {"Authorization": "Bearer key-OPENAI_API_KEY"})
        self.assertEqual((body["model"], body["voice"], body["response_format"], body["instructions"]), ("gpt-4o-mini-tts", "coral", "pcm", "A calm older sister"))
        self.assertAlmostEqual(audio.duration, 0.5 + 0.0, delta=0.15)

    def test_google_uses_the_voice_language(self):
        calls, patch = self.fake_http(lambda call: {"audioContent": base64.b64encode(tone(0.4)).decode()})
        with patch:
            tts.speak(self.root, "नमस्ते", {"provider": "google", "voice": "hi-IN-Neural2-A"}, "English")
        body = calls[0]["body"]
        self.assertTrue(calls[0]["url"].startswith("https://texttospeech.googleapis.com/v1/text:synthesize?key="))
        self.assertEqual((body["voice"], body["audioConfig"]["audioEncoding"]), ({"languageCode": "hi-IN", "name": "hi-IN-Neural2-A"}, "LINEAR16"))

    def test_gemini_is_directed_and_accepts_wav_or_pcm(self):
        tts.set_secret(self.root, "GEMINI_API_KEY", "key-GEMINI_API_KEY")
        replies = iter([{"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(tone(0.5)).decode()}}]}}]},
                        {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "audio/L16;codec=pcm;rate=24000",
                                                                            "data": base64.b64encode(tts.read_wav(tone(0.4)).samples.tobytes()).decode()}}]}}]}])
        calls, patch = self.fake_http(lambda call: next(replies))
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch:
            wav = tts.speak(self.root, "Your bill went up.", {"provider": "gemini", "voice": "Puck", "style": "A calm older sister.", "speed": 1.0}, "Hinglish")
            pcm = tts.speak(self.root, "Your bill went up.", {"provider": "gemini", "model": "gemini-3.8-flash-lite-tts", "speed": 1.1}, "English")
        first, second = calls
        self.assertEqual(first["url"], "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent")
        self.assertEqual(first["headers"], {"x-goog-api-key": "key-GEMINI_API_KEY"})
        config = first["body"]["generationConfig"]
        self.assertEqual((config["responseModalities"], config["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"]), (["AUDIO"], "Puck"))
        prompt = first["body"]["contents"][0]["parts"][0]["text"]
        self.assertTrue(prompt.startswith("A calm older sister."))
        self.assertIn("mixes Hindi and English", prompt)
        self.assertTrue(prompt.endswith("Say exactly this, and nothing else:\nYour bill went up."))
        self.assertIn("gemini-3.8-flash-lite-tts:generateContent", second["url"])
        self.assertIn("brisk pace", second["body"]["contents"][0]["parts"][0]["text"])
        self.assertAlmostEqual(wav.duration, 0.5, delta=0.01)
        self.assertEqual(pcm.rate, 24000)
        self.assertAlmostEqual(pcm.duration, 0.4, delta=0.01)
        self.assertEqual(len(tts.provider("gemini").voices(self.root, "Hindi")), 30)
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}), self.fake_http(lambda call: {"candidates": [{"finishReason": "SAFETY"}]})[1]:
            with self.assertRaisesRegex(tts.TTSError, r"no audio \(SAFETY\)"):
                tts.speak(self.root, "Hi.", {"provider": "gemini"}, "English")

    def test_missing_keys_and_tools_are_explained(self):
        tts.set_secret(self.root, "SARVAM_API_KEY", "")
        with self.assertRaisesRegex(tts.TTSError, "Add your Sarvam AI API key"):
            tts.speak(self.root, "hi", {"provider": "sarvam"}, "Hindi")
        with self.assertRaisesRegex(tts.TTSError, "Choose a voice provider"):
            tts.speak(self.root, "hi", {"provider": ""}, "Hindi")
        with mock.patch.object(tts.PiperProvider, "command", lambda self: None):
            self.assertIn("pip install piper-tts", tts.provider("piper").problem(self.root))
        listed = {p["id"]: p for p in tts.providers(self.root)}
        self.assertFalse(listed["sarvam"]["key_set"])
        self.assertTrue(listed["elevenlabs"]["key_set"])
        self.assertNotIn("key-ELEVENLABS_API_KEY", json.dumps(listed))

    def test_http_errors_carry_the_providers_message(self):
        error = urllib_error(401, b'{"detail": {"status": "invalid_api_key", "message": "Invalid API key"}}')
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(tts.TTSError, r"HTTP 401 \(check the API key\): Invalid API key"):
                tts.http_json("GET", "https://api.elevenlabs.io/v1/voices")


def urllib_error(code, body):
    import urllib.error
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(body))


@unittest.skipUnless(shutil.which("espeak-ng") or shutil.which("espeak") or (sys.platform == "darwin" and shutil.which("say")),
                     "needs espeak-ng (Linux) or say (macOS)")
class SystemVoiceTest(unittest.TestCase):
    def test_the_computer_speaks_english_and_hindi(self):
        with tempfile.TemporaryDirectory() as tmp:
            for language, text in (("English", "Your bill went up."), ("Hindi", "आपका बिल बढ़ गया.")):
                audio = tts.speak(Path(tmp), text, {"provider": "system", "speed": 1.0}, language)
                self.assertGreater(audio.duration, 0.5)
            self.assertTrue(tts.provider("system").voices(Path(tmp), "Hindi"))


class StudioVoiceoverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.fake = FakeProvider()
        self.registry = mock.patch.dict(tts.PROVIDERS, {"fake": self.fake})
        self.registry.start()
        with contextlib.redirect_stdout(io.StringIO()):
            studio.main(["--workspace", str(self.home), "new-project", "--name", "Voice"])
        studio.add_channel(self.home, {"name": "Shorts", "language": "Hinglish"})
        studio.add_channel(self.home, {"name": "WhatsApp", "kind": "post"})
        self.project = studio.Studio(self.home / "projects" / "voice", self.home)
        self.script = idea_script(self.project, "shorts")["id"]
        self.text = ("## Hook\nYour bill went up this month. [1]\nVisual: stat | 12% | Bill\n"
                     "## Price\nIt costs ₹6,500 now.\nSay: It costs sixty five hundred rupees now.\nVisual: text | Price\n"
                     "## Hold\nShort.\nDuration: 0.2\nVisual: text | Hold\n"
                     "## End\nVisual: end | Bye | Follow")
        self.project.update_script(self.script, {"text": self.text})

    def tearDown(self):
        self.registry.stop()
        self.tmp.cleanup()

    def test_settings_are_per_video_channel(self):
        self.assertEqual(studio.channel_narration(self.home, "shorts")["provider"], "")
        saved = studio.save_narration(self.home, "shorts", {"provider": "fake", "voice": "v"})
        self.assertEqual(studio.save_narration(self.home, "shorts", {"speed": 1.2})["voice"], "v")  # partial saves merge
        self.assertEqual(saved["pause"], 0.3)
        with self.assertRaises(ValueError):
            studio.save_narration(self.home, "whatsapp", {"provider": "fake"})
        with self.assertRaises(ValueError):
            studio.save_narration(self.home, "shorts", {"provider": "fake", "speed": 9})

    def test_beats_take_the_length_of_their_voice(self):
        script = self.project.script(self.script)
        self.assertEqual(script["narration"]["status"], "none")
        self.assertNotIn("audio", script["scenes"][0])
        with self.assertRaisesRegex(ValueError, "Choose a voice"):
            self.project.narrate_script(self.script)
        studio.save_narration(self.home, "shorts", {"provider": "fake", "voice": "v", "pause": 0.4})
        self.assertEqual(self.project.script(self.script)["narration"]["missing"], 3)
        self.assertEqual(self.project.narrate_script(self.script), {"made": 3, "beats": 3, "provider": "fake"})
        self.assertEqual([c[0] for c in self.fake.calls], ["Your bill went up this month.", "It costs sixty five hundred rupees now.", "Short."])
        self.assertEqual(self.fake.calls[0][2], "Hinglish")
        script = self.project.script(self.script)
        hook, price, hold, end = script["scenes"]
        self.assertEqual(hook["duration"], studio.beat_seconds(hook["audio"]["duration"], 0.4))
        self.assertAlmostEqual(hook["audio"]["duration"], 0.6, delta=0.01)  # six words, no silence to trim
        self.assertEqual(len(hook["audio"]["words"]), 6)
        self.assertNotIn("words", price["audio"])  # Say: differs from the captions, so captions spread by length
        self.assertEqual(hold["duration"], 1.0)  # a fixed Duration: wins (and its minimum is 1 s)
        self.assertNotIn("audio", end)
        self.assertEqual((script["narration"]["done"], script["narration"]["missing"], script["narration"]["status"]), (3, 0, "done"))
        self.assertEqual(script["duration"], studio.total_duration(script["scenes"]))
        warnings = studio.scene_warnings(script["scenes"])
        self.assertFalse(any("voiceover runs" in w for w in warnings))
        # unchanged beats are reused; an edited beat is the only one redone; unused clips are removed
        self.assertEqual(self.project.narrate_script(self.script)["made"], 0)
        self.project.update_script(self.script, {"text": self.text.replace("Short.", "A much longer line that keeps going and going, well past the one second this beat is held to on screen.")})
        self.assertEqual(self.project.narrate_script(self.script)["made"], 1)
        files = sorted(p.name for p in self.project.path("scripts", self.script, "narration").glob("*.wav"))
        self.assertEqual(len(files), 3)
        warnings = studio.scene_warnings(self.project.script(self.script)["scenes"])
        self.assertTrue(any("Hold: the voiceover runs" in w for w in warnings), warnings)
        # a new voice redoes every beat; force redoes them too
        studio.save_narration(self.home, "shorts", {"voice": "other"})
        self.assertEqual(self.project.script(self.script)["narration"]["missing"], 3)
        self.assertEqual(self.project.narrate_script(self.script)["made"], 3)
        self.assertEqual(self.project.narrate_script(self.script, force=True)["made"], 3)
        # turning the narrator off goes back to estimated timing
        studio.save_narration(self.home, "shorts", {"provider": ""})
        self.assertNotIn("audio", self.project.script(self.script)["scenes"][0])

    def test_a_failed_voiceover_keeps_the_clips_it_made(self):
        studio.save_narration(self.home, "shorts", {"provider": "fake"})
        real = self.fake.synthesize

        def flaky(root, text, settings, language):
            if text.startswith("It costs"):
                raise tts.TTSError("quota")
            return real(root, text, settings, language)
        with mock.patch.object(self.fake, "synthesize", flaky):
            with self.assertRaisesRegex(tts.TTSError, "quota"):
                self.project.narrate_script(self.script)
        narration = self.project.script(self.script)["narration"]
        self.assertEqual((narration["status"], narration["error"], narration["done"]), ("failed", "quota", 1))
        self.assertEqual(self.project.narrate_script(self.script)["made"], 2)

    def test_export_captions_and_cli(self):
        studio.save_narration(self.home, "shorts", {"provider": "fake"})
        self.project.narrate_script(self.script)
        folder = self.project.export_script(self.script)
        page = (folder / "index.html").read_text()
        self.assertEqual(page.count('<audio id="vo-'), 3)
        self.assertIn('data-start="0.000"', page)
        self.assertEqual(len(list((folder / "narration").glob("*.wav"))), 3)
        srt = self.project.captions_srt(self.script)
        self.assertTrue(srt.startswith("1\n00:00:00,"))
        self.assertIn("It costs ₹6,500 now.", srt)  # captions show what's written, not the Say: line
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            studio.main(["--workspace", str(self.home), "voice-providers"])
            studio.main(["--workspace", str(self.home), "narrate", "--script", self.script, "--force"])
            studio.main(["--workspace", str(self.home), "say", "--channel", "Shorts", "--text", "One two", "--out", str(self.home / "s.wav")])
        self.assertIn("fake · Fake · local · ready", out.getvalue())
        self.assertIn("3 of 3 beats voiced with fake", out.getvalue())
        self.assertAlmostEqual(tts.read_wav((self.home / "s.wav").read_bytes()).duration, 0.2, delta=0.01)
        with self.assertRaises(SystemExit):
            studio.main(["--workspace", str(self.home), "voice-key", "--provider", "sarvam"])
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(sys, "stdin", io.StringIO("sk-live\n")), mock.patch.dict(os.environ, {"SARVAM_API_KEY": ""}):
            studio.main(["--workspace", str(self.home), "voice-key", "--provider", "sarvam", "--key", "-"])
            self.assertEqual(tts.secret(self.home, "SARVAM_API_KEY"), "sk-live")

    @unittest.skipUnless(render.find_ffmpeg(), "needs ffmpeg")
    def test_the_mixed_track_is_exactly_as_long_as_the_video(self):
        studio.save_narration(self.home, "shorts", {"provider": "fake"})
        self.project.narrate_script(self.script)
        script = self.project.script(self.script)
        clips, start = [], 0.0
        for scene in script["scenes"]:
            if scene.get("audio"):
                clips.append((start, self.project.path("scripts", self.script, scene["audio"]["src"])))
            start += scene["duration"]
        track = render.mix_voiceover(clips, script["duration"], self.home / "vo.wav")
        with wave.open(str(track)) as handle:
            self.assertEqual((handle.getframerate(), handle.getnchannels()), (48000, 2))
            self.assertAlmostEqual(handle.getnframes() / 48000, script["duration"], places=2)

    def test_http_api(self):
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()

        def call(method, path, body=None, headers=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            try:
                sent = {"Host": "localhost", "X-Vid-Studio": "1", "Content-Type": "application/json", **(headers or {})}
                connection.request(method, path, json.dumps(body) if body is not None else None, sent)
                response = connection.getresponse()
                data = response.read()
                return response.status, (json.loads(data) if response.getheader("Content-Type", "").startswith("application/json") else data), response
            finally:
                connection.close()
        try:
            with mock.patch.dict(os.environ, {"SARVAM_API_KEY": ""}):
                code, listed, _ = call("PUT", "/api/voice-providers/sarvam/key", {"key": "sk-secret"})
                self.assertEqual(code, 200)
                self.assertTrue(next(p for p in listed if p["id"] == "sarvam")["key_set"])
                self.assertNotIn("sk-secret", json.dumps(call("GET", "/api/voice-providers")[1]))
            self.assertEqual(call("PUT", "/api/voice-providers/system/key", {"key": "x"})[0], 400)
            self.assertEqual(call("PUT", "/api/channels/shorts/narration", {"provider": "fake"})[1]["provider"], "fake")
            self.assertEqual(call("GET", "/api/channels/shorts/narration")[1]["provider"], "fake")
            self.assertEqual(call("PUT", "/api/channels/shorts/narration", {"speed": 5})[0], 400)
            self.assertEqual(call("GET", "/api/voice-providers/nope/voices")[0], 404)
            code, sample, _ = call("POST", "/api/channels/shorts/narration/sample", {"text": "One two three", "settings": {"voice": "x"}})
            self.assertEqual(code, 200)
            self.assertTrue(sample["audio"].startswith("data:audio/wav;base64,"))
            self.assertEqual(self.fake.calls[-1][:2], ("One two three", "x"))
            code, state, _ = call("POST", f"/api/p/voice/scripts/{self.script}/narrate", {})
            self.assertEqual(code, 200)
            studio.NARRATIONS[f"{self.project.ws}:{self.script}"].join(10)
            script = call("GET", f"/api/p/voice/scripts/{self.script}")[1]
            self.assertEqual(script["narration"]["status"], "done")
            src = script["scenes"][0]["audio"]["src"]
            code, whole, response = call("GET", f"/api/p/voice/scripts/{self.script}/{src}")
            self.assertEqual((code, response.getheader("Content-Type"), response.getheader("Accept-Ranges")), (200, "audio/wav", "bytes"))
            code, part, response = call("GET", f"/api/p/voice/scripts/{self.script}/{src}", headers={"Range": "bytes=10-19"})
            self.assertEqual((code, part, response.getheader("Content-Range")), (206, whole[10:20], f"bytes 10-19/{len(whole)}"))
            self.assertEqual(call("GET", f"/api/p/voice/scripts/{self.script}/{src}", headers={"Range": f"bytes={len(whole) + 5}-"})[0], 416)
            self.assertEqual(call("GET", f"/api/p/voice/scripts/{self.script}/narration/..%2Fscript.json")[0], 404)
            code, srt, response = call("GET", f"/api/p/voice/scripts/{self.script}/captions.srt")
            self.assertEqual(code, 200)
            self.assertIn(b"-->", srt)
            self.assertIn("attachment", response.getheader("Content-Disposition"))
        finally:
            server.shutdown()
            server.server_close()


class YourVoiceTest(unittest.TestCase):
    """Takes you record or upload, the "Your voice" narrator, and ElevenLabs voice cloning."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.fake = FakeProvider()
        self.registry = mock.patch.dict(tts.PROVIDERS, {"fake": self.fake})
        self.registry.start()
        with contextlib.redirect_stdout(io.StringIO()):
            studio.main(["--workspace", str(self.home), "new-project", "--name", "Voice"])
        studio.add_channel(self.home, {"name": "Shorts", "language": "English"})
        self.project = studio.Studio(self.home / "projects" / "voice", self.home)
        self.script = idea_script(self.project, "shorts")["id"]
        self.project.update_script(self.script, {"text": "## Hook\nYour bill went up.\nVisual: text | Up\n## Why\nThe tariff changed.\nSay: The tariff changed in October.\nVisual: text | Why\n## End\nVisual: end | Bye | Go"})

    def tearDown(self):
        self.registry.stop()
        self.tmp.cleanup()

    def test_a_take_wins_over_the_narrator_and_works_without_one(self):
        # no narrator: the take still times and voices its beat, and nothing counts as missing
        narration = self.project.add_take(self.script, "Your bill went up.", tone(1.2, 48000, lead=0.5, tail=0.5), "hook.wav", "uploaded")
        take = next(iter(narration["takes"].values()))
        self.assertEqual((take["source"], narration["recorded"], narration["missing"]), ("uploaded", 1, 0))
        self.assertAlmostEqual(take["duration"], 1.2 + 0.08 + 0.15, delta=0.03)  # silence trimmed, a breath kept
        hook = self.project.script(self.script)["scenes"][0]
        self.assertTrue(hook["audio"]["recorded"])
        self.assertEqual(hook["duration"], studio.beat_seconds(take["duration"], 0.3))
        # a narrator voices only the beats without a take
        studio.save_narration(self.home, "shorts", {"provider": "fake"})
        self.assertEqual(self.project.narrate_script(self.script)["made"], 1)
        self.assertEqual([c[0] for c in self.fake.calls], ["The tariff changed in October."])
        scenes = self.project.script(self.script)["scenes"]
        self.assertTrue(scenes[0]["audio"]["src"].startswith("narration/rec-"))
        self.assertNotIn("recorded", scenes[1]["audio"])
        # a take for a Say: line belongs to what's said
        self.project.add_take(self.script, "The tariff changed in October.", tone(0.8), "why.wav")
        self.assertEqual(self.project.script(self.script)["narration"]["recorded"], 2)
        self.assertEqual(self.project.narrate_script(self.script, force=True)["made"], 0)
        with self.assertRaisesRegex(ValueError, "isn't in the script"):
            self.project.add_take(self.script, "Something else.", tone(0.5))
        with self.assertRaisesRegex(tts.TTSError, "silent"):
            self.project.add_take(self.script, "Your bill went up.", tone(0.0, lead=1.0))
        key = tts.recording_key("Your bill went up.")
        self.project.delete_take(self.script, key)
        self.assertFalse(self.project.path("scripts", self.script, "narration", f"rec-{key}.wav").exists())
        with self.assertRaises(KeyError):
            self.project.delete_take(self.script, key)

    def test_your_voice_narrator_never_synthesises(self):
        studio.save_narration(self.home, "shorts", {"provider": "recorded"})
        narration = self.project.script(self.script)["narration"]
        self.assertEqual((narration["missing"], narration["done"]), (2, 0))
        with self.assertRaisesRegex(ValueError, "record or upload a take for: Hook, Why"):
            self.project.narrate_script(self.script)
        with self.assertRaisesRegex(tts.TTSError, "own voice"):
            studio.speak_sample(self.home, "shorts", "Hello")
        self.project.add_take(self.script, "Your bill went up.", tone(1.0))
        self.project.add_take(self.script, "The tariff changed in October.", tone(1.0))
        self.assertEqual(self.project.narrate_script(self.script), {"made": 0, "beats": 2, "provider": "recorded"})
        self.assertEqual(self.fake.calls, [])

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_browser_recordings_are_converted(self):
        source = self.home / "in.wav"
        source.write_bytes(tone(1.0, 44100, lead=0.3, channels=2))
        webm = self.home / "take.webm"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source), "-c:a", "libopus", str(webm)], check=True)
        narration = self.project.add_take(self.script, "Your bill went up.", webm.read_bytes(), "take.webm")
        wav = self.project.path("scripts", self.script, "narration", next(iter(narration["takes"].values()))["file"])
        audio = tts.read_wav(wav.read_bytes())
        self.assertEqual(audio.rate, 48000)
        self.assertTrue(0.95 <= audio.duration <= 1.3, audio.duration)  # the tone, a breath either side, Opus padding
        with self.assertRaisesRegex(tts.TTSError, "Couldn't read that audio"):
            tts.to_wav(b"definitely not audio", "x.mp3")

    def test_cli_take(self):
        path = self.home / "mine.wav"
        path.write_bytes(tone(0.9))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            studio.main(["--workspace", str(self.home), "take", "--script", self.script, "--beat", "2", "--file", str(path)])
            studio.main(["--workspace", str(self.home), "take", "--script", self.script, "--beat", "2", "--remove"])
        self.assertIn("Saved your take of Why", out.getvalue())
        self.assertIn("Removed your take of Why", out.getvalue())
        with self.assertRaises(SystemExit):
            studio.main(["--workspace", str(self.home), "take", "--script", self.script, "--beat", "3", "--file", str(path)])

    def test_clone_your_voice_with_elevenlabs(self):
        tts.set_secret(self.home, "ELEVENLABS_API_KEY", "xi-test")
        sent = []

        def http(method, url, headers=None, body=None, timeout=120):
            sent.append((method, url, headers, body))
            return json.dumps({"voice_id": "VoIcE123", "requires_verification": False}).encode(), "application/json"
        samples = [("one.wav", tone(15)), ("two.wav", tone(20, 22050))]
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}), mock.patch.object(tts, "http", http):
            with self.assertRaisesRegex(ValueError, "Confirm"):
                studio.clone_channel_voice(self.home, "shorts", "Me", samples, consent=False)
            with self.assertRaisesRegex(tts.TTSError, "at least 30 seconds"):
                studio.clone_channel_voice(self.home, "shorts", "Me", [("short.wav", tone(5))], consent=True)
            made = studio.clone_channel_voice(self.home, "shorts", "My narrator", samples, consent=True)
        method, url, headers, body = sent[-1]
        self.assertEqual((method, url, headers["xi-api-key"]), ("POST", "https://api.elevenlabs.io/v1/voices/add", "xi-test"))
        self.assertTrue(headers["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertEqual(body.count(b'name="files"'), 2)
        self.assertIn(b'name="name"\r\n\r\nMy narrator', body)
        self.assertIn(b'name="remove_background_noise"\r\n\r\ntrue', body)
        self.assertEqual((made["voice_id"], made["seconds"]), ("VoIcE123", 35.0))
        self.assertEqual((made["narration"]["provider"], made["narration"]["voice"]), ("elevenlabs", "VoIcE123"))
        self.assertEqual(len(list((self.home / "channels" / "shorts" / "voice-samples").iterdir())), 2)

    def test_http_takes_and_clone(self):
        server = studio.ThreadingHTTPServer(("127.0.0.1", 0), studio.make_handler(self.home))
        threading.Thread(target=server.serve_forever, daemon=True).start()

        def call(method, path, body=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            try:
                connection.request(method, path, json.dumps(body) if body is not None else None,
                                   {"Host": "localhost", "X-Vid-Studio": "1", "Content-Type": "application/json"})
                response = connection.getresponse()
                data = response.read()
                return response.status, (json.loads(data) if response.getheader("Content-Type", "").startswith("application/json") else data)
            finally:
                connection.close()
        try:
            data = "data:audio/wav;base64," + base64.b64encode(tone(1.0)).decode()
            code, narration = call("POST", f"/api/p/voice/scripts/{self.script}/takes", {"text": "Your bill went up.", "data": data, "name": "t.wav"})
            self.assertEqual((code, narration["recorded"]), (200, 1))
            take = next(iter(narration["takes"].values()))
            code, wav = call("GET", f"/api/p/voice/scripts/{self.script}/narration/{take['file']}")
            self.assertEqual((code, wav[:4]), (200, b"RIFF"))
            self.assertEqual(call("POST", f"/api/p/voice/scripts/{self.script}/takes", {"text": "Your bill went up.", "data": "%%%"})[0], 400)
            key = take["file"][4:16]
            self.assertEqual(call("DELETE", f"/api/p/voice/scripts/{self.script}/takes/{key}")[1]["recorded"], 0)
            code, reply = call("POST", "/api/channels/shorts/voice-clone", {"name": "Me", "samples": [], "consent": True})
            self.assertEqual((code, reply["error"]), (409, "Add your ElevenLabs API key"))
        finally:
            server.shutdown()
            server.server_close()


@unittest.skipUnless(shutil.which("node"), "Node is needed to check the browser's narration timing")
class NarrationParityTest(unittest.TestCase):
    def test_preview_times_voiced_beats_like_the_server(self):
        ui = (Path(__file__).resolve().parents[1] / "skills/vid-studio/assets/ui/index.html").read_text()
        parser = ui[ui.index("const SCENE_TYPES ="):ui.index("// One preview at a time:")]
        helper = ui[ui.index("function withNarration("):ui.index("const scriptScenes =")]
        text = "## A\nOne two three.\n## B\nFour.\nSay: Four, said slowly.\n## C\nFive six.\nDuration: 2\n## D\nUnvoiced line here."
        scenes = studio.parse_scenes(text, 160)
        clips = {"One two three.": {"file": "a.wav", "duration": 1.234, "words": [[0, .3], [.3, .6], [.6, 1.2]], "caption": "One two three."},
                 "Four, said slowly.": {"file": "b.wav", "duration": 0.05, "words": None, "caption": "Four."},
                 "Five six.": {"file": "c.wav", "duration": 2.5, "words": None, "caption": "Five six."}}
        narration = {"provider": "fake", "pause": 0.35, "clips": clips}
        clips["Unvoiced line here."] = {"file": "rec-d.wav", "duration": 2.0, "words": None, "caption": "Unvoiced line here.", "recorded": True}
        expected = json.loads(json.dumps(scenes))
        for scene in expected:
            clip = clips.get(scene.get("say") or scene["vo"])
            if clip:
                scene["audio"] = {"src": "narration/" + clip["file"], "duration": clip["duration"]} | ({"recorded": True} if clip.get("recorded") else {})
                if clip["words"] and clip["caption"] == scene["vo"]:
                    scene["audio"]["words"] = clip["words"]
                if not scene.get("fixed"):
                    scene["duration"] = studio.beat_seconds(clip["duration"], 0.35)
        program = parser + helper + f"\nprocess.stdout.write(JSON.stringify(withNarration(parseScenes({json.dumps(text)}, 160), {json.dumps(narration)})));"
        preview = json.loads(subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(preview, expected)
        self.assertEqual([s["duration"] for s in preview], [1.6, 1.5, 2.0, 2.4])
        # takes apply even when the channel has no narrator
        alone = subprocess.run(["node", "-e", parser + helper + f"\nprocess.stdout.write(JSON.stringify(withNarration(parseScenes({json.dumps(text)}, 160), {json.dumps({'provider': '', 'pause': 0.3, 'clips': {'Unvoiced line here.': clips['Unvoiced line here.']}})})));"],
                               capture_output=True, text=True, check=True)
        self.assertTrue(json.loads(alone.stdout)[3]["audio"]["recorded"])


if __name__ == "__main__":
    unittest.main()
