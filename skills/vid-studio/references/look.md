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
  "colors": {"background": "#121212", "surface": "#1E1E1E", "text": "#F7F3EA", "muted": "#9C978D",
             "accent": "#FFC233", "accent2": "#FF7A45", "negative": "#FF5D5D"},
  "fonts": {"display": "Bricolage Grotesque", "body": "Mukta", "mono": "JetBrains Mono"},
  "type": {"scale": 1.0, "display_case": "none", "display_weight": 800, "tracking": -0.03},
  "motion": {"energy": "high", "easing": "snappy", "transition": "slide"},
  "captions": {"style": "highlight", "position": "lower", "highlight": "accent", "max_words": 4, "size": "medium"},
  "background": {"style": "aura", "pattern": "none"},
  "cards": {"style": "glass"},
  "images": {"treatment": "dim", "layout": "auto"},
  "sources": {"show": true},
  "progress": {"show": true},
  "radius": 28,
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
| `captions.style` | `none`, `plain`, `boxed`, `karaoke` (words light up as spoken), `highlight` (a pill in the highlight colour slides behind the word being spoken; the default), `underline` (a bar in the highlight colour sits under the spoken word; quieter, for editorial looks), or `pop` (one or two words at a time, big) |
| `captions.position` | `lower`, `middle`, or `upper` |
| `captions.highlight` | `accent`, `accent2`, or `text` |
| `captions.max_words` | Words per caption line, 1–8 |
| `captions.size` | `small`, `medium`, or `large`. Captions carry the words while videos have no voiceover, so `medium` or `large` |
| `cards.style` | `glass` (the default): each idea sits on one rounded pane tinted from the text colour, with a hairline edge lit from the top and a long soft shadow; over a full-screen photo the pane blurs the photo behind it. `solid`: the same panes filled with `surface`. `flat`: no panes; type, hairlines and photos edge to edge (Swiss uses it) |
| `images.layout` | Where beat photos go: `auto` (above a stat, punchline, quote, list, message, title or end card, sized to what the scene leaves, or down the left side in wide formats; full-screen behind charts) or `full` (always full-screen behind the scene). With cards the photo above is a rounded photo card in front of the same photo, blurred, so the whole frame takes its colours; flat looks run it edge to edge. A beat can choose with `Image: path \| credit \| top` or `\| full` |
| `images.treatment` | How beat photos (`Image:` lines) look: `natural`, `dim` (darkened for legible text), `mono` (black and white), or `duotone` (tinted from the background color to the accent, so photos from different sources look like one brand) |
| `sources.show` | `true` shows each beat's `Source:` line as one line of small print at the very bottom of the frame; `false` hides them |
| `progress.show` | `true` draws a thin progress line at the top, one segment per beat, filling as the voiceover plays |
| `background.style` | `aura` (three soft fields of light in `accent`, `accent2` and the text colour, which move to new places at each scene change and hold still while a scene plays; the default, and what makes glass read as glass), `solid` (flat colour), `grain` (fine film grain), `paper` (paper texture), or `gradient` (a barely visible tonal step from the top; no look uses it) |
| `background.pattern` | `none`, `grid`, `dots`, or `lines` |
| `radius` | Corner radius of cards and photo cards in px at 1080 wide (0–48); bars, tiles and pills scale from it. 24–34 reads as soft and modern; flat looks use 0–8 and keep photos square |
| `logo.text` / `logo.position` | A text wordmark shown small on every scene (empty for none); `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `custom_css` | Extra CSS for the composition, for anything the keys can't express. Scenes use CSS variables like `--accent` and classes like `.scene-stat .value`; keep it small. |

## Taste

Clean, minimal, and finished. One pane per idea, one accent, and nothing that does not carry information.

- **One card per idea.** A stat, a chart, a quote, a message thread, the end card: each sits on one rounded pane. A list gives each point its own row card. Nothing is nested more than one level, and no scene has a second decorative card.
- **Glass is quiet.** The pane is a faint tint with a hairline edge and one long shadow. It blurs only what is sharp behind it (a full-screen photo); over the aura it is a clean tint. No glows, coloured shadows, neon edges or reflections.
- **Type does the hierarchy.** The thing that matters in each scene (the number, the subject of a comparison, the tallest bar, the spoken word) takes the accent and full-strength type; everything else is text or muted. The accent's soft gradient appears only on the subject's bar, the reply bubbles and the call to action.
- **Photos are photography.** A photo above a scene is a rounded photo card at full colour, in front of the same photo blurred, so every photo scene takes its palette from its picture. Don't frame photos twice, tint them by hand or run text across them.
- **Light moves between scenes, not during them.** The aura glides at each scene change; holds stay still.

Translate feelings into these settings. "More premium": a quieter palette with one accent, a serif or a tight grotesque for display, `medium` or `calm` energy, `fade` transitions, `underline` captions (Frost, Night Edition). "Like a newspaper": Clean Newsroom (solid cards). "Information design": Swiss (flat, square corners, hard cuts). "Louder": `highlight` or `pop` captions, `high` energy. "Softer" or "more rounded": a larger `radius`. "Glass" or "frosted": `cards.style: glass` with the `aura` background.

Headlines read better in sentence case (`display_case: none`); keep `upper` for condensed display faces. Check that `accent` reads on `background` (contrast 3:1 or more for big numbers) and that `text` reads at 4.5:1.
