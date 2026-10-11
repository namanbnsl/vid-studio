# Write or revise a script

A script is one story made for one channel. The prompt names one script, like `"Title" (script-id)`, or a story and a list of script IDs ("write the scripts for the story …: id1, id2"). Each script's files are in `scripts/<id>/`:
- `script.json`: the title, the `story` it comes from, the `channel` it is for, and its `stage`
- `script.md`: the text you write (a video script, or a text post for post channels)
- `comments.json`: the user's comments on the text (use `studio.py comments`, below)

The channel is in `channels.json` at the studio root (`studio.py channels` lists them): its `kind` (`video` or `post`), `platform`, `language`, `audience`, and `format`.

## Write a draft

1. Read the story's `notes.md` in `stories/<story>/`. **If it's empty, research the story first** ([story.md](story.md)), so every script shares one research pass. When writing several scripts for one story, research once, then write each.
2. Read the channel. Write in its `language` (see the language rule in SKILL.md) and follow its `format`: structure, length, tone, and visual notes. Write for its `audience` if set, else the project's.
   - **Video** (`kind: video`): markdown (the studio renders it). Cite facts inline with the notes' source numbers, like `[1]`.
   - **Post** (`kind: post`): WhatsApp formatting only: `*bold*`, `_italic_`, and plain URLs. The post must stand alone, and should end with source links.
3. Use only facts in the notes. If the script needs a fact the notes lack, verify it and add it, with its source, to the notes. Present contested points as contested.
4. **Respect the user's edits.** If `script.md` already has text, rewrite only when the prompt asks for a rewrite. Otherwise, improve what's there and keep their wording where it works.
5. Write `script.md`. Never change `stage`; the user moves scripts through stages.

## Revise with comments

The user comments on passages of the text in the studio. "Revise the script …" means: address its open comments.

1. Run `studio.py comments --script ID`. It lists the open comments **in the order they appear in the text**, each with the passage it's on (its `quote`), or "on the whole script". Work through them in that order.
2. For each one, make the change in `script.md`. Change only what the comment asks; keep everything else as it is. If a comment needs a new fact, verify it and add it to the story's notes.
3. After addressing each, run `studio.py resolve --script ID --comment C --reply "one line on what you changed"`. If you disagree with a comment or can't do it, leave it open and say why in your reply to the user.
4. A comment whose quote is "no longer in the text" was on a passage that has since changed; apply it to wherever that passage went, or leave it open and say so.

Reply with a two-line summary (and which comments you resolved) and the studio link. The UI picks up the changes on its own.

For an edit request in chat ("make the hook punchier", "shorten the post"), change only what was asked.
