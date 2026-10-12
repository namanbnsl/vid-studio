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
  "colors": {"background": "#0E0E10", "surface": "#1A1A1F", "text": "#F5F5F0", "muted": "#9A9AA2",
             "accent": "#FFD23F", "accent2": "#3DDC97", "negative": "#FF5A5F"},
  "fonts": {"display": "Anton", "body": "Mukta", "mono": "JetBrains Mono"},
  "type": {"scale": 1.0, "display_case": "upper", "display_weight": 800, "tracking": -0.01},
  "motion": {"energy": "high", "easing": "snappy", "transition": "slide"},
  "captions": {"style": "karaoke", "position": "lower", "highlight": "accent", "max_words": 4},
  "background": {"style": "grain", "pattern": "grid"},
  "radius": 18,
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
| `captions.style` | `none`, `plain`, `boxed`, `karaoke` (words light up as spoken), or `pop` (one word at a time, big) |
| `captions.position` | `lower`, `middle`, or `upper` |
| `captions.highlight` | `accent`, `accent2`, or `text` |
| `captions.max_words` | Words per caption line, 1–8 |
| `background.style` | `solid`, `gradient`, `grain`, or `paper` |
| `background.pattern` | `none`, `grid`, `dots`, or `lines` |
| `radius` | Corner radius of cards and bars, in px at 1080 wide (0–48) |
| `logo.text` / `logo.position` | A text wordmark shown small on every scene (empty for none); `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `custom_css` | Extra CSS for the composition, for anything the keys can't express. Scenes use CSS variables like `--accent` and classes like `.scene-stat .value`; keep it small. |
