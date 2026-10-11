# Vid Studio

Research for your video channels, managed by the `vid-studio` skill. Open the studio with `python3 <skill>/scripts/studio.py serve`, or ask your agent: "Use vid-studio, open the studio".

Each channel has its own folder in `channels/<channel>/`:

- `studio.json`: channel name, audience, language, research schedule, and your script and WhatsApp post formats.
- `topics.json`: what the channel makes videos about.
- `sources.json`: websites every research run must check, plus sources research has suggested.
- `findings.json`: what research found, each finding linked to its topics and sources.
- `runs.json`: the history of research runs.
- `scripts/<id>/`: one folder per script, containing `script.json`, `script.md`, `post.md`, and `notes.md`.

To delete a channel, delete its folder. Everything here is plain files, so you can edit them by hand.
