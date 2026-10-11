# WhatsApp post and video script

Inputs: the project's `brief.md` and `claims.json`, plus `studio.json` → `format`, `language`, `audience`, and `format.examples`. Write in the configured language and tone.

## Script (`script.md`)

1. **Titles.** Write three options that follow `format.title_rules`, then put the best one first. Each title must be something the video actually delivers.
2. **Beats.** Use exactly the beats in `format.structure`, in order, with their target seconds. Scale the timing to `format.video_seconds`. Each beat contains:
   - **Voiceover.** Written for the ear: short sentences, one idea each. Use about 2.5 spoken words per second, so a 90-second video is roughly 220 words. End every factual sentence with its claim IDs, like `[C3]`. Use only `verified` or `single-source` claims. Attribute single-source numbers out loud ("according to Reuters…"). Present `disputed` claims as contested.
   - **On screen.** The text overlay, if any, in a few words.
   - **Visual.** Give one of these types, plus a description and its source:
     - `chart`: name the `data/*.csv` file, the chart type, and the single point it makes.
     - `real asset`: the URL of an official photo, a document, a map, footage, or a screenshot, with its credit or licence note. Prefer official and public-domain sources.
     - `graphic`: a diagram or animation explaining the mechanism, described step by step.
     - `text card`: a quote or number, with the claim ID.
3. **Hook.** Lead with the most surprising verified fact or a sharp question. Do not make a promise the script fails to keep.
4. **Takeaway.** One sentence the viewer could repeat to a friend.
5. **Sources.** End with a numbered list of the cited sources: publisher, title, date, and URL.

## WhatsApp post (`post.md`)

Follow `format.whatsapp`. The post must stand alone, for people who never watch the video:

- A `*bold*` title.
- 2-4 short paragraphs or bullets: what happened, why it matters, and the key number.
- A one-line takeaway.
- 1-3 source links.

Use WhatsApp formatting only: `*bold*`, `_italic_`, and plain URLs. Respect `max_words` and the emoji preference.

Below the `---` line, keep the claim map, which lists the claim IDs behind each paragraph. That section is for checking and is not part of the message.

## Self-review

Before showing the drafts, reread both against this list:

- Every factual sentence has a claim, and each claim's `quote` actually says it.
- The numbers, units, and dates match the claim ledger exactly.
- The main caveat or uncertainty from the brief is mentioned.
- The script fits the length, follows the beat structure, and suits the audience's level. Jargon is explained or removed.
- No hype words the evidence doesn't support.

Run `studio.py check PROJECT`. Fix all ERRORs. Then run `studio.py stage ID script-review`.

## Review and edits

Show the user the chosen title, the script's voiceover (beat by beat, compact), the post, and any WARNs you accepted.

Then apply their edits:

- **Wording, tone, or structure edits.** Edit the files directly and show only what changed.
- **Edits that add or change a fact.** Verify the fact first: capture a source and add or update the claim. If it cannot be verified, say so and suggest wording that fits the evidence.
- **Persistent preferences** ("always…", "never…"). Also update `studio.json` → `format`, so future scripts follow them.

When the user approves, run `studio.py stage ID approved --note "approved by user"`. Report the file paths. The approved `script.md` (with its visual plan and `data/`) is the hand-off to video production. Production is out of scope for this skill.

In scheduled runs, stop at `script-review`. List the script in the digest as waiting for review.
