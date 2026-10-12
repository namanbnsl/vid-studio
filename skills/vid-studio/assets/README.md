# Vid Studio

Research and scripts for your videos, managed by the `vid-studio` skill. Open the studio with `python3 <skill>/scripts/studio.py serve`, or ask your agent: "Use vid-studio, open the studio".

The UI has three global tabs: Research, Production, and Channels. Research contains projects and their evidence. Production collects scripts from every project, with links to their source stories and destination channels. Channels is shared and can be set up independently.

`channels.json` lists where you publish (each YouTube channel, Instagram account, or WhatsApp channel), with its language and format. Every project shares it.

`channels/<id>/design.json` stores a video channel's look (fonts, colors, motion, captions, and logo). `voice.json` stores its script preferences (length, pace, tone, rules, and example scripts). Change either in Channels → Look or Voice, or describe a change in Ask your agent.

Each project has its own folder in `projects/<project>/`:

- `studio.json`: project name, audience, and research schedule.
- `topics.json`: what the project makes videos about.
- `sources.json`: websites every research run must check, plus sources research has suggested.
- `findings.json`: what research found, each finding linked to its topics and sources.
- `runs.json`: the history of research runs.
- `stories/<id>/`: one folder per story, containing `story.json` and the research notes in `notes.md`.
- `scripts/<id>/`: one folder per script (a story made for one channel), containing `script.json`, `script.md`, `comments.json`, hook alternatives in `angles.json`, and a self-review in `review.json`. Video beats preview live in the channel's look; `studio.py export --script ID` creates a HyperFrames project in `render/`.

To delete a project, delete its folder. Everything here is plain files, so you can edit them by hand.
