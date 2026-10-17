# Images for a script

A photo behind the right beats is what makes a video look produced instead of templated. Each image lives with its script in `scripts/<id>/media/` and is used from a beat:

```markdown
## Hook
Jaquar के नए sensor नल ₹6,500 से शुरू होते हैं… [1]
Visual: stat | ₹6,500 | Jaquar sensor tap | starting price
Image: media/sensor-tap.jpg | Photo: BPE innovationas / Wikimedia Commons, CC BY-SA 4.0
```

- `Image: path | credit` gives that beat a photo. On a title, the photo fills the frame under a light veil and the title sits over it near the bottom (with tiles). On a stat, punchline, quote, list, message or end card, the photo sits across the top of the frame as a rounded photo card, as tall as the scene below it allows; in wide formats it takes the left side. (Flat looks run it edge to edge with a hard edge instead.) On a chart, it fills the screen behind the scene, veiled, and the chart's tile frosts the part it covers. Add `| top` or `| full` at the end of the line to choose for yourself.
- `Visual: image | what it shows | path | credit` makes the photo itself the scene, for beats where seeing the thing *is* the point. Without a path, it's an "Image needed" card in the preview, and the render warns about it.
- The credit shows small on the photo (or at the bottom of the frame). Keep it short: `Photo: Name / Source, License`.
- Because photos usually take the top of the frame rather than the full 1080×1920, a 1024 px photo looks sharp. An `image` scene whose photo is too small to fill the screen runs across the top instead of being blown up.

## Which beats get a photo

Two to four photos in a 60-second script is usually right; `studio.py scenes` warns when a video of 30 seconds or more has none. Use them for beats about **real, specific things**: a product, a place, a building, an institution, a screen in an app, a document, a person's role ("a plumber fitting a CPVC pipe").

**Put people in the frame.** Hands on a phone, a shopkeeper at a counter, a vegetable market, a street, a family at home: photos of people and everyday places are what make a video feel made by people. Use them for the real things the findings are about: the product, the counter, the screen. They're illustrative, so never imply that the people shown are the people in the findings, and never use a photo of an identifiable person for a beat about wrongdoing.

Leave out beats that are about numbers or mechanisms alone; the scene is stronger there.

## Where photos come from

Work down this list for each beat and stop at the first that gives you a good, honest picture.

1. **The user's own images.** If the fact sheet or the user point at photos they own (product shots, screenshots), use those.
2. **A real, openly licensed photo.** Search with `studio.py images "query" --orientation tall --preview /tmp/vid-images` (use `wide` for 16:9 channels). It searches Wikimedia Commons and Openverse for photos you can use commercially and modify (CC0, public domain, CC BY, CC BY-SA), and saves small previews. **Look at the previews before choosing.** Query with concrete nouns ("sensor tap bathroom sink", "Reserve Bank of India building Mumbai"), not ideas ("saving water"). Prefer photos at least 1080 px on the short side.
3. **An image you generate**, if an image-generation tool is available in the current agent session. Save the file and add it like any other. If no such tool is available, use a licensed photo or a scene without a photo.
4. **No photo.** A good scene without a photo beats a wrong or fake-looking one.

Then save it to the script and use the path it prints:

```sh
studio.py media --script ID --add "https://upload.wikimedia.org/…/Sensor_Tap.jpg" --name sensor-tap \
  --credit "Photo: BPE innovationas / Wikimedia Commons, CC BY-SA 4.0" --source "https://commons.wikimedia.org/wiki/File:Sensor_Tap.jpg"
studio.py media --script ID --add ./generated/kitchen-tap.png --name kitchen-tap --credit "AI-generated illustration"
```

`studio.py media --script ID` lists a script's images; `--remove FILE` deletes one. The user can also add a photo to any beat from the script page (the image button on each beat).

## Rules for generated images

Generated images are for **generic, illustrative scenes**: a kitchen tap running, a hand holding a phone, a stack of coins, a city street at dusk. Write the prompt like a photo brief: subject, setting, light, lens, vertical 9:16 (or the channel's aspect), no text in the image.

Never generate:
- **Real, identifiable people** (a minister, a CEO, a creator), or anyone presented as a real person in the findings.
- **Real products, brands, logos, or packaging** ("a Jaquar tap", "the PhonePe app"). A generated version is a fake product shot; use a real photo or none.
- **Documents, screenshots, charts, or anything that looks like evidence** (a circular, a bank SMS, a news page).
- **Events from the findings** ("the factory fire", "the launch event").

Credit generated images as `AI-generated illustration` so the video never passes one off as a photograph.

## Licences and credits

- Only use photos whose licence allows commercial use and modification: CC0, public domain, CC BY, or CC BY-SA. `studio.py images` only returns these; if you find a photo elsewhere, check its page.
- Always pass `--credit` and `--source` for photos you didn't make. The credit shows on screen, and `studio.py render` lists every credit so the user can paste them into the video description.
- Never use a photo from a news site, a stock site's watermarked preview, or a search engine's image results.
