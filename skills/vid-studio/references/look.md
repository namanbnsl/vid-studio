# Channel look

Each video channel has a **look**: colors, fonts, motion, captions, and background, used by every scene in its videos. It lives in `channels/<channel-id>/design.json` at the studio root. The user designs it in the studio (Channels → a channel → Look) with a live preview, or asks you to change it.

## Change a look

1. Read the current look with `studio.py design --channel ID` (or the JSON file).
2. Change only what the user asked. Keep the rest. If they describe a feeling ("more premium", "like Bloomberg", "louder"), translate it into concrete values and say which you changed and why.
3. Save with `studio.py design --channel ID --file new.json` (or `-` for stdin). The helper validates it, fills missing keys from the preset, and the open studio updates its preview within seconds.
4. If the channel language is Hindi or Hinglish, the display and body fonts must support Devanagari (`devanagari: true` in `studio.py fonts`).
5. Reply with what changed and the studio link to the channel's Look tab.

To start from a preset, `studio.py presets` lists them; set `"preset"` and drop the keys you want the preset to decide.

## design.json

```json
{
  "preset": "bold-explainer",
  "aspect": "9:16",
  "colors": {"background": "#121110", "surface": "#1D1B19", "text": "#F7F3EA", "muted": "#9C978D",
             "accent": "#FFC233", "accent2": "#FF7A45", "negative": "#FF5D5D"},
  "fonts": {"display": "Bricolage Grotesque", "body": "Mukta", "mono": "JetBrains Mono"},
  "type": {"scale": 1.0, "display_case": "none", "display_weight": 800, "tracking": -0.03},
  "motion": {"energy": "high", "easing": "snappy", "transition": "slide"},
  "captions": {"style": "highlight", "position": "lower", "highlight": "accent", "max_words": 4, "size": "medium"},
  "background": {"style": "ambient", "pattern": "none"},
  "surfaces": {"style": "glass"},
  "images": {"treatment": "dim", "layout": "auto"},
  "sources": {"show": true},
  "progress": {"show": true},
  "radius": 16,
  "logo": {"text": "PIPE GYAAN", "position": "top-left"},
  "custom_css": ""
}
```

| Key | Values |
|---|---|
| `aspect` | `9:16` (Shorts, Reels), `16:9` (YouTube), `1:1`, `4:5` |
| `colors.*` | Hex colors. `accent` is the hero color (numbers, highlights); `accent2` is secondary; `negative` marks falls and warnings. Keep text readable on `background` (contrast 4.5:1 or more). |
| `fonts.display` / `body` / `mono` | Font family names from `studio.py fonts` (Google Fonts). `display` for titles and numbers, `body` for labels and captions, `mono` for data. |
| `type.scale` | 0.8–1.3, multiplies all text sizes |
| `type.display_case` | `upper`, `title`, or `none` |
| `type.display_weight` | 400–900 |
| `type.tracking` | Letter spacing for display text, in em (-0.05 to 0.1) |
| `motion.energy` | `calm`, `medium`, or `high`: how fast and how much things move |
| `motion.easing` | `smooth`, `snappy`, or `bouncy` |
| `motion.transition` | Between scenes: `cut`, `fade`, `slide`, `zoom`, or `wipe` |
| `captions.style` | `none`, `plain`, `boxed`, `karaoke` (words light up as spoken), `highlight` (a pill in the highlight colour slides behind the word being spoken; the default), `glass` (the same pill, inside a frosted caption box that stays legible over photos), or `pop` (one or two words at a time, big) |
| `captions.position` | `lower`, `middle`, or `upper` |
| `captions.highlight` | `accent`, `accent2`, or `text` |
| `captions.max_words` | Words per caption line, 1–8 |
| `captions.size` | `small`, `medium`, or `large`. Captions carry the words while videos have no voiceover, so `medium` or `large` |
| `surfaces.style` | The panels that charts, stats, lists, quotes, messages and end cards sit on: `glass` (frosted and translucent, with a hairline edge; it picks up the light or photo behind it), `solid` (the `surface` colour), or `flat` (no panels: type and data straight on the background) |
| `images.layout` | Where beat photos go: `auto` (framed above a stat, punchline, quote, list, title or end card, over a blurred copy of the photo; full-screen behind charts and messages) or `full` (always full-screen behind the scene). A beat can choose with `Image: path \| credit \| card` or `\| full` |
| `images.treatment` | How beat photos (`Image:` lines) look: `natural`, `dim` (darkened for legible text), `mono` (black and white), or `duotone` (tinted from the background color to the accent, so photos from different sources look like one brand) |
| `sources.show` | `true` shows each beat's `Source:` line as one line of small print at the very bottom of the frame; `false` hides them |
| `progress.show` | `true` draws a thin progress line at the top, one segment per beat, filling as the voiceover plays |
| `background.style` | `ambient` (three very soft fields of light in the accent colours, drifting a little at each beat, with fine grain; what glass needs to look like glass), `solid` (flat colour), `gradient` (a barely visible tonal step from the top), `grain` (fine film grain), or `paper` (paper texture) |
| `background.pattern` | `none`, `grid`, `dots`, or `lines` |
| `radius` | Corner radius, in px at 1080 wide (0–48). Panels use about 2.75× this (capped at 56 px), bars and chips less |
| `logo.text` / `logo.position` | A text wordmark shown small on every scene (empty for none); `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `custom_css` | Extra CSS for the composition, for anything the keys can't express. Scenes use CSS variables like `--accent` and classes like `.scene-stat .value`; keep it small. |

## Taste

Premium is restraint with depth. The looks are built from a few layers, and each has one job:

- **Light** (`background.style: ambient`): soft fields of the accent colours, low and slow, so the frame never feels like a dead slide. Never a neon glow, never a rainbow.
- **Surfaces** (`surfaces.style`): frosted glass panels that hold the information. Glass needs something behind it, so pair it with `ambient` or photos. Over a flat background, use `solid`.
- **Photos** (`images.layout: auto`): real photos framed like a magazine, with the content's panel overlapping the frame's lower edge and a blurred copy of the photo behind everything. This is what makes a video look produced rather than templated, so encourage photos ([images.md](images.md)).
- **Type and one accent**: the thing that matters in each scene (the number, the highlighted bar, the spoken word, the subject panel) takes the accent; everything else is text or muted.

Translate feelings into these layers. "More premium": `ambient` + `glass`, a quieter accent, `medium` or `calm` energy, `fade` transitions, `glass` captions. "Like Bloomberg": `solid` panels, `radius` 2–4, a sharp grotesque, `cut` transitions. "Handmade": `flat`, `paper`. Frosted Night and Daylight are the reference premium looks (dark and light).

Headlines read better in sentence case (`display_case: none`); keep `upper` for condensed display faces. Check that `accent` reads on `background` (contrast 3:1 or more for big numbers) and that `text` reads at 4.5:1; in light looks, check the accent on white glass too.
