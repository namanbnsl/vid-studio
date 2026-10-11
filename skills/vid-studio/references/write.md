# Write a draft

The prompt names a script, like `"Title" (script-id)`. Its files are in `scripts/<id>/`:
- `script.json`: the title, linked `findings` (IDs in `findings.json`), and linked `topics` (IDs in `topics.json`)
- `script.md`: the video script
- `post.md`: the WhatsApp post
- `notes.md`: research notes

A script can be one of three kinds:
- **News:** findings only. The story is the development; research what happened, why, and what it means.
- **Explainer:** topics only. Research the subject from scratch: background, how it works, the key numbers, and current state. Use reference sources such as official explainers, company or regulator pages, papers, data, and good encyclopedic overviews.
- **Both:** a news hook leading into an explainer. Use the findings for the hook and the topic for the depth.

## Steps

1. Read the linked findings and topics, along with `studio.json`: `audience`, `language`, `script_format`, and `post_format`. If nothing is linked, work from the title.
2. **Research in depth.** Open the findings' sources, and go further wherever the story needs it: primary documents, data, background, opposing views. Check the facts the script will rely on, especially numbers and dates.
3. **Write `notes.md`.** Record what you learned, organised however suits the story. End with a numbered source list (`[1] Publisher, title, date, URL`) covering every source you cite. Note anything uncertain or disputed.
4. **Write `script.md`.** Follow `script_format`: its structure, length, tone, and visual notes. Cite facts inline with the source numbers, like `[1]`. Present contested points as contested.
5. **Write `post.md`.** Follow `post_format`, using WhatsApp formatting only: `*bold*`, `_italic_`, and plain URLs. The post must stand alone, and should end with source links.
6. **Respect the user's edits.** If `script.md` or `post.md` already has text the user wrote, rewrite only when the prompt asks for a rewrite. Otherwise, improve what's there and keep their wording where it works.
7. Reply with a two-line summary and the studio link. The UI picks up the new files on its own.

For an edit request ("make the hook punchier", "shorten the post"), change only what was asked. If the edit brings in a new fact, verify it and add its source to the notes.
