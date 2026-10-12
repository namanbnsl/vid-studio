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
```

- `## Name`: the beat's name (Hook, Context, How it works, …). It is a label for the team, never shown or spoken.
- **Voiceover:** every other plain line is spoken, in order. Write it exactly as it should be said. Citations like `[1]` are kept for review but are not spoken and not counted for timing.
- `Visual: TYPE | field | field …`: the scene shown during this beat. One per beat; if a beat needs two visuals, split it into two beats.
- `Text: …`: optional extra on-screen text (a short overlay, under 8 words).
- `Note: …`: optional production note for the team (not shown, not spoken).
- Anything before the first `##` (like a `# Title`) is ignored.

A beat without a `Visual:` line shows its voiceover as a big caption (`text` scene).

The parser accepts indented beat headings, optional Markdown emphasis around cue labels, and `-` or `*` bullets before cues. Nested headings and the preamble are ignored. An empty `Visual:` or `Visual: text` uses the spoken line as its caption; an empty `Note:` is omitted. Numeric citations (including ranges) are removed after Markdown links become their visible labels, so linked numbers remain spoken. The browser preview and export use the same rules.

## Timing

A beat lasts as long as its voiceover takes to say: spoken words ÷ the channel's words per minute (from its voice settings; 160 if unset), with a minimum of 1.5 seconds. Count words after removing citations and markdown. `studio.py scenes --script ID` prints each beat with its scene and timing, and the total; use it to hit the channel's target length.

## Scene types

Fields are separated by `|`, in this order. Trailing fields are optional. Numbers may include units and symbols (`₹5,000`, `42%`, `3.2 lakh`); the scene animates the number part.

| Type | Fields | Use it for |
|---|---|---|
| `title` | title \| subtitle \| kicker | Opening or section title |
| `stat` | value \| label \| context | One big number that carries the beat |
| `bars` | title \| Label: value \| Label: value … | 2–6 values to compare as a bar chart |
| `compare` | title \| Label: value \| Label: value | Before/after, this vs that (exactly two) |
| `list` | title \| item \| item … | 2–5 short points, steps, or reasons |
| `quote` | quote \| source | A real quote from a source in the notes |
| `timeline` | title \| date: label \| date: label … | 2–5 dated events in order |
| `text` | text | A punchline or key sentence, big on screen |
| `image` | description \| url | A real photo, screenshot, or clip; description says what to show |
| `end` | title \| call to action | The last beat |

Example `Visual:` lines:

```
Visual: title | Your story, explained | 60 seconds | Source-backed explainer
Visual: bars | Example volumes | Period 1: 36 | Period 2: 52 | Period 3: 64
Visual: list | The mechanism | First step | Second step | Third step
Visual: quote | Exact words from an opened source | Source name and date
Visual: image | Close-up of a UPI Lite screen on a phone
Visual: end | Follow for one money rule a day | Follow @explainedin90s
```

Keep on-screen words few: titles under 6 words, labels under 4, list items under 6. The voiceover explains; the screen shows the one thing to remember.
The examples above demonstrate syntax. Replace their figures and placeholder quote with evidence from the story's notes.

## Scene JSON

The studio parses beats into this shape (the UI, the player, and `studio.py scenes --json` all use it):

```json
{"beat": "Hook", "type": "stat", "duration": 3.4, "vo": "UPI Lite की limit अब ₹5,000 है…", "text": "₹2,000 → ₹5,000",
 "data": {"value": "₹5,000", "label": "UPI Lite wallet limit", "context": "was ₹2,000"}}
```

`data` keys per type: `title` {title, subtitle, kicker} · `stat` {value, label, context} · `bars` {title, items: [{label, value}]} · `compare` {title, items: [{label, value}] (two)} · `list` {title, items: [string]} · `quote` {quote, source} · `timeline` {title, items: [{date, label}]} · `text` {text} · `image` {description, url} · `end` {title, cta}. In `bars` and `compare`, `value` is the original text (`"₹1,000"`); the player extracts the number. An unknown type becomes `image` with the whole line as its description.
