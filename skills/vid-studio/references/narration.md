# Voiceover (text to speech)

A video channel can have a **narrator**: a text-to-speech voice that reads every script on the channel. With one, each beat's voiceover is recorded as its own clip, the beat lasts as long as the clip (plus a short pause), captions follow the voice, and the rendered MP4 carries the voiceover instead of silence. Without one (the default), videos render silent and beats are timed by the channel's words per minute.

## Providers

`studio.py voice-providers` lists them and whether each is ready on this machine.

| Provider | Runs | Needs | Good for |
|---|---|---|---|
| `system` | on this computer | macOS `say` or Linux `espeak-ng` | Checking timing for free; robotic |
| `piper` | on this computer | `pip install piper-tts`; each voice downloads once (~60 MB) | Free, offline, natural English and Hindi |
| `elevenlabs` | cloud | `ELEVENLABS_API_KEY` | The most natural voices, cloned voices; word-timed captions |
| `sarvam` | cloud | `SARVAM_API_KEY` | Indian voices for Hindi, Hinglish and Indian English |
| `openai` | cloud | `OPENAI_API_KEY` | Voices that follow speaking instructions (the channel's persona) |
| `google` | cloud | `GOOGLE_TTS_API_KEY` (Text-to-Speech enabled) | Chirp 3 HD and Neural2 voices in Hindi and Indian English |

Cloud providers receive the script text. Keys come from the environment first, then the studio's `.secrets.json` (readable only by the user). The user adds keys in the UI (Channels → Voice providers); in chat, use `studio.py voice-key --provider P --key -` and pipe the key in, so it doesn't land in the shell history. Never print, log, or repeat a key.

## Choose a voice for a channel

The user normally does this in the UI (Channels → the channel → Narration), where they can hear samples. From chat:

1. `studio.py voices --provider P --language Hinglish` lists the voices and the default for that language.
2. Save the settings with `studio.py narration --channel C --file -`:

   ```json
   {"provider": "sarvam", "voice": "anushka", "speed": 1.0, "pause": 0.3, "lexicon": {"UPI": "U P I"}}
   ```

   - `provider`: one of the ids above, or `""` for no voiceover.
   - `voice`, `model`: empty means the provider's default (`studio.py voices` shows it). ElevenLabs takes any voice id on the account, including cloned voices.
   - `speed` (0.7–1.3) and `pause` (seconds of air after each beat, 0–1.5).
   - `style`: how to speak, for providers that take instructions (OpenAI). Empty uses the channel's persona.
   - `lexicon`: whole words and how to say them, for every script on the channel: acronyms, brand names, words the voice gets wrong.
3. `studio.py say --channel C --text "…" --out sample.wav` speaks a line so the user can listen.

Pick the provider and voice the user asked for. If they haven't chosen, suggest one (Sarvam or ElevenLabs for Hindi and Hinglish; ElevenLabs or OpenAI for English; `system` only to check timing) and let them choose; never sign them up for a paid service on your own.

## Make the voiceover

`studio.py narrate --script S` records every beat that has no current clip: a clip is reused until the beat's words or the channel's voice settings change, so a revision only re-records the beats you touched. `--force` redoes all of them. Rendering does this on its own first. The UI's script page shows how many beats are voiced and has the same buttons.

After narrating, run `studio.py scenes --script S`: the timings are now the real ones. A beat with a `Duration:` line keeps its fixed length; if the voice runs longer, it gets cut off and `scenes` warns, so remove the `Duration:` or shorten the line.

## Write for the ear

- Write the voiceover exactly as it should sound, as script-craft.md already asks. Numbers the way people say them help any voice.
- When the voice should say something different from what the captions show, add `Say:` under the beat. The captions keep the written line; the voice reads the `Say:` line. Use it for numbers and symbols ("₹12,000" → "बारह हज़ार रुपये"), abbreviations read as words, or a name the voice mispronounces once. For a word that recurs across scripts, add it to the channel's `lexicon` instead.

```markdown
## The price
ये नल ₹6,500 से शुरू होते हैं. [1]
Say: ये नल साढ़े छह हज़ार रुपये से शुरू होते हैं.
Visual: stat | ₹6,500 | Jaquar sensor नल | शुरुआती क़ीमत
```

## Files

`scripts/<id>/narration/` holds one WAV per beat (named by what was said and how) and `narration.json`, which lists them with their lengths and, from ElevenLabs, word timings. Rendering writes `render/voiceover.wav` (the mixed track, loudness-normalised for phones) and `render/captions.srt`; `studio.py captions --script S --out file.srt` writes the captions on their own, for uploading to YouTube or an editor.
