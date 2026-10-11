# Vid Studio workspace

One channel's research, managed by the `vid-studio` skill. Open the studio with `python3 <skill>/scripts/studio.py serve`, or ask your agent: "Use vid-studio, open the studio".

- `studio.json`: channel name, audience, language, research schedule, and your script and WhatsApp post formats.
- `topics.json`: what you follow. Each topic has a name and a description; the description guides relevance.
- `sources.json`: websites checked on every research run, for all topics.
- `findings.json`: what research found. Each finding has a summary, its topics, and its sources.
- `runs.json`: the history of research runs.
- `scripts/<id>/`: one folder per script, containing `script.json` (title and attached findings), `script.md`, `post.md`, and `notes.md` (research notes and sources).

All of these are plain files, so you can edit them by hand.
