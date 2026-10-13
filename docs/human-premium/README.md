# Human stories, editorial scenes

The videos were accurate and clean, but they still felt made by a machine. The scripts explained topics rather than telling anyone's story, and the frames were type on a background with no pictures of real things. This change works on both, from the research step to the rendered frame.

- **Content:** research and story notes now gather the people a story lands on, the everyday moment they meet it, and what they actually ask. Scripts are about someone, carry a point of view the evidence earns, and are scored and linted for it.
- **Design:** an editorial print system. Flat colour, type, hairlines and real photographs, with no gradients, glass, blur or shadows. Photos run edge to edge across the top of the frame like the picture on a magazine page. A folio counts the beats, the spoken word can be underlined rather than boxed, a new scene shows the call or text a story turns on, and there are two new looks.

Every image below was rendered by the real scene engine at 1080×1920 (or 1920×1080 and 1080×1080). "Before" is `main`'s engine, presets and examples; "after" is this branch.

## Before and after

### English example (Bold Explainer)

![English example, before and after](assets/english-before-after.jpg)

### Same script, same photos: the engine alone

The rewritten English script rendered on `main`'s engine, then on this branch's. The difference here is design only: on `main` a photo can only sit dimmed behind a scene.

![Same script on the old and new engine](assets/same-script-engine.jpg)

### Motion: the first 15 seconds

Old on the left, new on the right. The photo is revealed with a clean wipe and pushes in slowly; everything else is the old engine's restrained motion.

![English opening, before and after](assets/english-hook-before-after.gif)

### Hinglish example (Night Desk)

![Hinglish example, before and after](assets/hinglish-before-after.jpg)

The call the story turns on is now on screen, as a labelled reconstruction, under a photo of a hand on a phone. The bubbles arrive one by one, each after a moment of typing dots:

![The call, animated](assets/hinglish-call.gif)

### Hindi example (Monsoon)

![Hindi example, before and after](assets/hindi-before-after.jpg)

## What changed in the writing

The three bundled examples set the bar every agent reads before drafting, so they were rewritten around a person and a moment. The facts, citations and arithmetic are unchanged, and all three are within ±10% of their target length with no lint warnings.

| | Before | After |
|---|---|---|
| English hook | "One lakh at twelve percent earns more in its last ten years than in its first twenty." | "Put one lakh away at twenty-five, and it earns most of its money after you turn forty-five." Then the moment that makes people quit: "Five years in, you open the app, and your one lakh has turned into about one point eight." |
| English view | (none) | "The reason is boring, honestly." "I picked twelve percent to keep the maths clean." |
| Hinglish stakes | "Call आता है: 'Sir, refund भेज दिया है, बस approve करके PIN डाल दो.'" | "मान लो पापा के phone पर call आता है. आवाज़ बिल्कुल bank वाली, और बात बड़े आराम से." The call is shown as a `message` scene, and the trap and the payoff come back to पापा. |
| Hinglish end | "ये Reel उसे भेजो जो हर refund approve कर देता है." | "ये Reel घर के group में भेज दो. Scammer से पहले आप पहुँच जाओ." |
| Hindi hook | "बजट के लिए स्प्रेडशीट नहीं चाहिए, बस तीन नंबर याद रखो…" | "सैलरी बीस तारीख़ तक ख़त्म? स्प्रेडशीट नहीं चाहिए, बस तीन नंबर याद रखो…" |
| Hindi history | "ये नियम 2005 की एक किताब से मशहूर हुआ…" | "ये नियम एक माँ और बेटी ने लिखा था, Elizabeth Warren और Amelia Warren Tyagi ने…" (true, and from the cited source) |

### Upstream, where the human material comes from

A writer can't invent a real person or moment at draft time, and must not. So the change starts in research:

- **`research.md`** reads the feed the way the audience would. Every finding says who it lands on, and runs listen to where the audience talks (forums, comment threads, complaint sites, help pages) for leads to follow to citable pages. Findings are written "like a person telling a colleague", not a press release.
- **`story.md`** has a new section, "Research the people, not just the facts", and a fixed shape for notes: angle, the people (real cases, who decided it, who disagrees), the moment, what people believe and ask (in their words), the facts, numbers, tension, what the viewer can do, exact quotes, and pictures to find.
- **`setup.md`** asks who's talking on each channel and saves it as the persona; topics are described from the audience's side.

### Script craft

- **New §3, "The person and the moment":** choose who the video is about (a sourced case, the viewer in a moment, an openly hypothetical relative, or the decision-maker), carry them through to the payoff, put the viewer somewhere specific, have a point of view the facts earn, never fake experience, and respect the viewer.
- **A `moment` hook style** ("It's the twentieth, and your salary account says three thousand"), plus new re-hooks (returning to the person) and new machine-made patterns: invented characters, fake anecdotes, lecture voice, talking to a crowd, "Imagine…" openers, mock suspense.
- **A ninth rubric score, `human`** ("Human story" in the studio), next to `natural` ("Sounds human"). It asks whether the video is about someone, carried through, with a lived detail and an earned view.
- The default voice, the default video format and `SKILL.md` carry the same rule: real cases, the viewer, or openly hypothetical people, never invented ones.

### The linter catches it

`studio.py scenes` now flags invented characters, fake anecdotes, "not X, it's Y" reframes, em-dash piles, talking to "guys", sentence rhythm that never varies, a video of 30 seconds or more with no photos, and a message that isn't labelled as an example or sourced. On a deliberately machine-made script:

```
Hook: "imagine a world" sounds machine-made; say the fact itself
Hook: "Meet Rahul" reads as an invented character; use a sourced case, "you", or "say your…"
Story: "my friend" is a personal story; keep it only if it really happened to the persona, otherwise use a sourced case or "say you…"
Story: a "not X, it's Y" reframe; just say what it is and why it matters
Story: 2 em dashes; that's written rhythm, so split or join the sentences the way you'd say them
Story: label the message: "Text: Example" for a reconstruction, or a Source: line for a real one
End: "follow for more" sounds machine-made; say the fact itself
```

## What changed in the design

Less is more. An earlier round of this branch tried frosted glass panels, ambient light fields and blurred photo backgrounds; they read as generated, so they're gone. No look uses a gradient, a glow, a blur or a drop shadow; the only shadow left is a soft one behind text set over a photo, so it stays legible. The look comes from four things:

- **Photography.** On a stat, punchline, quote, list, message, title or end card, the beat's photo runs edge to edge across the top of the frame with a hard edge, at full colour. Its height is whatever the scene leaves: the engine measures the content and gives the photo the rest, between 30% and 58% of the frame. The photo is revealed with a wipe and pushes in slowly. In 16:9 and 1:1 it fills the left side, and that beat's text, captions and source line move into the right-hand column. On a chart the photo sits full-screen behind, faint under the background colour. An `image` scene's photo fills the frame, untouched, with captions on a plain band of the background colour; if the photo is too small to fill the frame without going soft (most openly licensed photos are about 1024 px), it runs across the top instead. Any beat can choose with `Image: path | credit | top` or `| full`.
- **Type and one accent.** The subject of a comparison is set at full strength with an accent rule; the other side is muted. Two phrases are now two rows divided by hairlines that share the frame's height, instead of two small boxes.
- **A grid and a folio.** Labels are small capitals led by a short rule. The progress line is thinner and ends in a folio, like a page number (`03 / 08`).
- **The message scene** (`Visual: message | sender | line | you: reply | …`): flat bubbles under a small-caps sender line, arriving one by one.

Captions gain an `underline` style: a bar in the accent under the spoken word, quieter than a highlight pill. Calm Minimal, Broadsheet and the two new looks use it.

### Twelve looks

Each look renders the same three scenes here: a photo stat, a chart and the message scene. Two are new: **Night Edition** (soft black, warm paper-white, Fraunces serif headlines, one brass accent) and **Swiss** (off-white, black, signal red, Inter Tight set tight, square corners, hard cuts). The other ten keep their palettes and type from `main`.

![All twelve looks](assets/looks-after.jpg)

Before, on `main` (no photos, no message scene):

![The ten looks before](assets/looks-before.jpg)

### Wide formats

![16:9 and 1:1 frames](assets/wide-frames.jpg)

### In the studio

The Look editor gains Photo placement (Across the top, Full screen), the Underline caption style and the two new looks. The live preview sample is rewritten around a person ("Say you're twenty-five") and now has photos and a message scene, so every look is judged with real images in it.

![Look editor](assets/look-editor.jpg)

## Photos

The examples, the demo studio and the look previews ship with eight photos in `skills/vid-studio/assets/scenes/samples/` (about 830 KB in total). All are licensed CC BY 2.0 by their photographers and were found through Google's Open Images dataset, which records each photo's licence, author and Flickr page; `CREDITS.md` lists them. They are credited on screen wherever they appear. The comparison images in this folder crop, dim and overlay them.

## Checks

```sh
python3 -m unittest discover tests            # 40 tests; VID_STUDIO_RENDER_TEST=1 adds the real MP4 render
node --test tests/test_ui.js tests/test_engine.js
git diff --check
```

New tests cover the voice lint (invented people, anecdotes, reframes, em dashes, rhythm, missing photos, unlabelled messages), `message` and photo-placement parsing in both parsers (the parity test), placement, caption and folio settings in the engine, and that every preset merges into a complete, valid look with fonts from the catalog. The demo script also went through the real renderer: 38.7 s at 720p, H.264, in 113 s, with its photo credits listed.
