# Script format and scenes

Video scripts (`kind: video`) use a light markdown format that the studio turns into **scenes**: animated, on-brand screens in the channel's look. The same scenes drive the live preview in the studio and, later, the rendered video. Text posts (`kind: post`) don't use this format.

## Beats

A script is a list of **beats**. Each beat starts with a level-2 heading and holds what is said and what is shown:

```markdown
## Hook
इस number का आपके लिए क्या मतलब है? [1]
Visual: stat | 42% | Example figure | replace with sourced data
Text: Example only

## Comparison
यहाँ source में दिए हुए before और after figures समझाओ. [1]
Visual: compare | Example comparison | Before: 500 | Now: 1000
Image: media/example-photo.jpg | Photo: Name / Wikimedia Commons, CC BY 4.0
Source: Example source, 1 Oct 2026
```

- `## Name`: the beat's name (Hook, Context, How it works, …). It is a label for the team, never shown or spoken.
- **Voiceover:** every other plain line is spoken, in order. Write it exactly as it should be said. Citations like `[1]` are kept for review but are not spoken and not counted for timing.
- `Visual: TYPE | field | field …`: the scene shown during this beat. One per beat; if a beat needs two visuals, split it into two beats.
- `Text: …`: optional extra on-screen text (a short overlay, under 8 words).
- `Note: …`: optional production note for the team (not shown, not spoken).
- `Image: path | credit`: optional photo for this beat. The path is one of the script's images (`media/…`, from `studio.py media`) or an `https://` URL. On a stat, punchline, quote, list, message, title or end card it sits across the top of the frame as a rounded photo card, sized to the space the scene leaves, in front of the same photo blurred, and the scene sits below it (in wide formats it takes the left side and the text the right; flat looks run it edge to edge); on a chart it fills the screen behind, and the chart's glass card blurs it. Add `| top` or `| full` at the end to choose. See [images.md](images.md).
- `Source: …`: optional short name of where this beat's fact comes from ("RBI circular, 1 Oct 2026"). It shows small on screen, unless the channel's look turns source tags off.
- `Duration: 4`: optional fixed length in seconds (1–60), instead of the length the voiceover takes. Use it for a beat with little or no voiceover that needs time on screen.
- `Say: …`: optional; what the voiceover speaks when it should differ from the captions ("₹12,000" said as "twelve thousand rupees"). Captions keep the written line. See [narration.md](narration.md).
- Anything before the first `##` (like a `# Title`) is ignored.

A beat without a `Visual:` line shows its voiceover as a big caption (`text` scene).

The parser accepts indented beat headings, optional Markdown emphasis around cue labels, and `-` or `*` bullets before cues. Nested headings and the preamble are ignored. An empty `Visual:` or `Visual: text` uses the spoken line as its caption; an empty `Note:` is omitted. Numeric citations (including ranges) are removed after Markdown links become their visible labels, so linked numbers remain spoken. The browser preview and export use the same rules.

## Timing

A beat lasts as long as its voiceover takes to say: spoken words ÷ the channel's words per minute (from its voice settings; 160 if unset), with a minimum of 1.5 seconds. When the channel has a narrator and the beat has been voiced ([narration.md](narration.md)), it lasts as long as the recorded clip plus the channel's pause instead. A `Duration:` line overrides both. Count words after removing citations and markdown. `studio.py scenes --script ID` prints each beat with its scene and timing, and the total; use it to hit the channel's target length.

## Scene types

Fields are separated by `|`, in this order. Trailing fields are optional. Numbers may include units and symbols (`₹5,000`, `42%`, `3.2 lakh`); the scene animates the number part.

| Type | Fields | Use it for |
|---|---|---|
| `title` | title \| subtitle \| kicker | Opening or section title |
| `stat` | value \| label \| context | One big number that carries the beat |
| `bars` | title \| Label: value \| Label: value … | 2–6 values to compare as a bar chart |
| `compare` | title \| Label: value \| Label: value | Before/after, this vs that (exactly two). The **second** item is the subject (the after, the new thing, the claim) and takes the accent. Two numbers draw bars; two short phrases draw side-by-side panels |
| `list` | title \| item \| item … | 2–5 short points, steps, or reasons |
| `quote` | quote \| source | A real quote from a source in the notes |
| `timeline` | title \| date: label \| date: label … | 2–5 dated events in order |
| `text` | text | A punchline or key sentence, big on screen |
| `image` | description \| path \| credit | A photo or screenshot as the whole scene; the description says what it shows (it's the brief while the image is missing, and the alt text after). A photo too small to fill the screen runs across the top instead of being blown up |
| `message` | sender \| line \| line … | The call, text or notification the story turns on, as chat bubbles on a phone card (1–4 lines). Lines starting `you:` are the viewer's replies, on the right. Label a reconstruction with `Text: Example` and a real message with its `Source:` |
| `end` | title \| call to action | The last beat |

Example `Visual:` lines:

```
Visual: title | Your story, explained | 60 seconds | Source-backed explainer
Visual: bars | Example volumes | Period 1: 36 | Period 2: 52 | Period 3: 64
Visual: list | The mechanism | First step | Second step | Third step
Visual: quote | Exact words from an opened source | Source name and date
Visual: image | Close-up of a UPI Lite screen on a phone | media/upi-lite-screen.png | Screenshot: NPCI
Visual: message | Unknown number | Sir, your refund is ready | you: Which refund? | Just approve it and enter your PIN
Visual: end | Follow for one money rule a day | Follow @explainedin90s
```

Keep on-screen words few: titles under 6 words, labels under 4, list items under 6. The voiceover explains; the screen shows the one thing to remember.

Every scene sits on one grid, and fills it. A thin progress line runs across the top, one rounded segment per beat, with a folio at its end (`03 / 08`). A `Text:` overlay (a small pill) and a chart's title share a header row pinned under it, in the same place in every scene. Below it, each idea sits on one rounded card in the channel's look (`cards.style`: glass by default, solid, or flat for no cards): a stat and its context on one card, a chart on one card, each list point and each timeline date on a row card, two phrases in a compare on two cards with a small arrow from the first to the second, a quote under a large opening mark, a message as a chat thread with the sender's initial, and the end card with a pill-shaped call to action. A stat, a punchline, a quote or the end card is centred in the space; charts, lists and timelines fill it. Behind everything, the `aura` background's soft light moves to a new place at each scene change. Captions sit in their own band, centred, with the spoken word highlighted, and the `Source:` line and photo credit are one line of small print on the bottom edge of the safe area. Holds are still, and headings keep one size across scenes, so write titles that fit in two lines rather than relying on the player to shrink them. `bars` with short labels (up to 12 characters, like years) draw columns; longer labels draw horizontal rows.

`studio.py scenes` warns about what makes a video look or sound generated: the same headline on screen twice, more than two `text` scenes, bars without numbers, a compare mixing a number with a phrase, chart values with no unit, an unlabelled message, no photos in a video of 30 seconds or more, and in the voiceover the phrases, invented characters, fake anecdotes, reframes, fragment chains and flat rhythm in script-craft.md. Fix every warning.
The examples above demonstrate syntax. Replace their figures and placeholder quote with evidence from the story's notes.

## Scene JSON

The studio parses beats into this shape (the UI, the player, and `studio.py scenes --json` all use it):

```json
{"beat": "Hook", "type": "stat", "duration": 3.4, "vo": "UPI Lite की limit अब ₹5,000 है…", "text": "₹2,000 → ₹5,000",
 "data": {"value": "₹5,000", "label": "UPI Lite wallet limit", "context": "was ₹2,000"}}
```

`data` keys per type: `title` {title, subtitle, kicker} · `stat` {value, label, context} · `bars` {title, items: [{label, value}]} · `compare` {title, items: [{label, value}] (two)} · `list` {title, items: [string]} · `quote` {quote, source} · `timeline` {title, items: [{date, label}]} · `text` {text} · `image` {description, url, credit} · `message` {title (the sender), items: [string]} · `end` {title, cta}. A beat with an `Image:` line also has `"image": {"src", "credit"}` (plus `"layout": "top"|"full"` when the line chose one), and one with a `Source:` line has `"source"`. A `Duration:` line adds `"fixed": true` and a `Say:` line adds `"say"`. A voiced beat has `"audio": {"src": "narration/….wav", "duration", "words"?}`, where `words` (from providers that report them) holds `[start, end]` seconds for each word of `vo`. In `bars` and `compare`, `value` is the original text (`"₹1,000"`); the player extracts the number. An unknown type becomes `image` with the whole line as its description.

## Render

`studio.py render --script ID` renders the video to `scripts/<id>/render/video.mp4` (1080p, 30 fps, H.264) on this machine, with Chrome and ffmpeg, recording the channel's voiceover first if it has a narrator; `--out ~/Desktop` also copies it there, and `--draft` renders a faster 720p check. It prints the image credits for the video description. The user can do the same from the script page (Render MP4, then Download MP4). `studio.py export --script ID` writes the same composition as a [HyperFrames](https://github.com/heygen-com/hyperframes) project instead.
