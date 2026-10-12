# Write or revise a script

A script is one story made for one channel. The prompt names one script, like `"Title" (script-id)`, or a story and a list of script IDs ("write the scripts for the story …: id1, id2"). Each script's files are in `scripts/<id>/`:
- `script.json`: the title, the `story` it comes from, the `channel` it is for, and its `stage`
- `script.md`: the text you write (a video script, or a text post for post channels)
- `comments.json`: the user's comments on the text (use `studio.py comments`, below)
- `angles.json`, `review.json`: the hook options and the self-review, saved with `studio.py angles` and `studio.py review`
- `media/`: the script's images, added with `studio.py media` ([images.md](images.md))

**Read [script-craft.md](script-craft.md) before writing anything.** It holds the process, the craft rules, the banned phrases, and the rubric. The bar is set by `assets/examples/`.

## Write a draft

1. **Research first.** Read the story's `notes.md` in `stories/<story>/`. If it's empty, research the story first ([story.md](story.md)), so every script shares one research pass. When writing several scripts for one story, research once, then write each one.
2. **Read the channel.** Run `studio.py channels` for its `kind`, `platform`, `language`, `audience` (else the project's), and `format`. Run `studio.py voice --channel C` for its length, words per minute, persona, tone, hook styles, `do`/`dont`, open/close/CTA, and examples. Write in the channel's `language` (SKILL.md's language rule).
3. **Follow script-craft.md §1, in order:** angle → the person and the moment → 3–5 hooks → pick one and save them all with `studio.py angles --script ID --file -` → talk it through → outline against `format` and `length_seconds` → draft → photos and sources ([images.md](images.md)) → time with `studio.py scenes --script ID` → remove the machine-made patterns → score → revise until every score is ≥ 8 → save with `studio.py review --script ID --file -`.
   - **Video** (`kind: video`): use the beat format in [scenes.md](scenes.md) exactly: `## Beat`, spoken lines, one `Visual: TYPE | fields` per beat, optional `Text:`, `Image:`, `Source:`, `Duration:` and `Note:`, and an `end` scene last. Cite facts inline with the notes' source numbers, like `[1]`.
   - **Post** (`kind: post`): WhatsApp formatting only (`*bold*`, `_italic_`, plain URLs). The post must stand alone and end with source links. See script-craft.md §12.
4. **Use only facts in the notes.** If the script needs a fact the notes lack, verify it and add it, with its source, to the notes. Present contested points as contested.
5. **Respect the user's edits.** If `script.md` already has text, rewrite it only when the prompt asks for a rewrite. Otherwise, improve what's there and keep their wording where it works. Score their text honestly too.
6. **Write `script.md`.** Never change `stage`; the user moves scripts through stages.
7. **Render only when asked.** If the user asks for the video ("render it", "make the MP4", "download"), run `studio.py render --script ID` (a few minutes) and share the file path and the image credits. Otherwise, tell them they can render it from the script page.

## Rewrite with the chosen angle

In the UI, the user can pick a different hook card. The prompt then says "rewrite … with the chosen angle". Read `angles.json` and find the angle with `chosen: true`. Rewrite `script.md` around that hook and angle: the hook line, the open loop, the beats that serve it, and the payoff that answers it. Keep the facts, and keep any passages the user wrote that still fit. Don't re-save `angles` (that would reset their choice) unless they ask for new options. Then re-time it, re-score it, and save a new review.

## Revise with comments

The user comments on passages of the text in the studio. "Revise the script …" means: address its open comments.

1. Run `studio.py comments --script ID`. It lists the open comments **in the order they appear in the text**, each with the passage it's on (its `quote`), or "on the whole script". Work through them in that order.
2. For each one, make the change in `script.md`. Change only what the comment asks; keep everything else as it is. If a comment needs a new fact, verify it and add it to the story's notes.
3. After addressing each, run `studio.py resolve --script ID --comment C --reply "one line on what you changed"`. If you disagree with a comment or can't do it, leave it open and say why in your reply to the user.
4. A comment whose quote is "no longer in the text" was on a passage that has since changed. Apply it to wherever that passage went, or leave it open and say so.
5. Re-run `studio.py scenes` (fix the timing if the edits pushed it off target) and save a fresh `studio.py review`. Comments can lower a score. If they do, say so.

Reply with a two-line summary (with the review scores, and which comments you resolved) and the studio link. The UI picks up the changes on its own.

For an edit request in chat ("make the hook punchier", "shorten the post"), change only what was asked, then re-time it and update the review.
