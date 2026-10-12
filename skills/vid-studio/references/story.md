# Research a story

The prompt names a story, like `"Title" (story-id)`. Its files are in `stories/<id>/`:
- `story.json`: the title, linked `findings` (IDs in `findings.json`), and linked `topics` (IDs in `topics.json`)
- `notes.md`: the research notes you write

A story is research, not a script. Every script made from it, on any channel, reads these notes, so research once and well. Notes are always in English.

A story can be one of three kinds:
- **News:** findings only. The story is the development; research what happened, why, and what it means.
- **Explainer:** topics only. Research the subject from scratch: background, how it works, the key numbers, and current state. Use reference sources such as official explainers, company or regulator pages, papers, data, and good encyclopedic overviews.
- **Both:** a news hook leading into an explainer. Use the findings for the hook and the topic for the depth.

## Steps

1. Read the linked findings and topics, and `audience` and `research_notes` in `studio.json`. If nothing is linked, work from the title.
2. **Research in depth.** Open the findings' sources, and go further wherever the story needs it: primary documents, data, background, opposing views. Check the facts a script will rely on, especially numbers and dates.
3. **Write `notes.md`** as markdown. Lead with the angle in one or two sentences: why this matters to the audience now. Then record what you learned, organised however suits the story, including the numbers worth showing on screen. End with a numbered source list (`[1] Publisher, title, date, URL`) covering every source you cite. Note anything uncertain or disputed.
4. **Respect the user's edits.** If `notes.md` already has text, add to it and correct it; don't throw it away unless the prompt asks for a fresh start.
5. Reply with a two-line summary and the studio link. Mention that the user can send the story to production from the story page.
