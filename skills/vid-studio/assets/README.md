# Vid Studio

Research and scripts for your videos, managed by the `vid-studio` skill. Open the studio with `python3 <skill>/scripts/studio.py serve`, or ask your agent: "Use vid-studio, open the studio".

`channels.json` lists where you publish (each YouTube channel, Instagram account, or WhatsApp channel), with its language and format. Every project shares it.

Each project has its own folder in `projects/<project>/`:

- `studio.json`: project name, audience, and research schedule.
- `topics.json`: what the project makes videos about.
- `sources.json`: websites every research run must check, plus sources research has suggested.
- `findings.json`: what research found, each finding linked to its topics and sources.
- `runs.json`: the history of research runs.
- `stories/<id>/`: one folder per story, containing `story.json` and the research notes in `notes.md`.
- `scripts/<id>/`: one folder per script (a story made for one channel), containing `script.json`, `script.md`, and `comments.json`.

To delete a project, delete its folder. Everything here is plain files, so you can edit them by hand.
