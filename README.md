# Vid Studio

A skill for running an explainer-video channel's research with any AI agent that supports [skills](https://skills.sh/), such as Claude, ChatGPT, or Codex. All data stays in a local folder, and you work in a small web UI.

```sh
npx skills add namanbnsl/vid-studio
```

## How it works

A workspace is one channel. It has four parts:

- **Topics:** what you follow. Each one is a name plus a description of what matters.
- **Sources:** websites checked on every research run, for all topics.
- **Findings:** new developments that research found, each with a summary, its topics, and its sources.
- **Scripts:** a title, the findings you attached, the video script, a WhatsApp post, and research notes.

You manage topics, sources, and scripts in the UI. The two steps that need an AI each have a button:

- **Research now** copies a prompt. Paste it into Claude or ChatGPT; your agent researches every topic and the new findings show up in the UI.
- **Write draft** (in a script) copies a prompt; your agent researches the attached findings in depth and writes the script, the post, and research notes.

To research every day, set times under **Schedule** and create a scheduled task in your agent app with the prompt shown there.

## Start

> Use vid-studio to set up my channel.

Your agent creates the workspace (`~/vid-studio` by default), proposes topics and sources, and opens the studio at `http://localhost:8765`. Later, "Use vid-studio, open the studio" brings it back.

## Files

```
skills/vid-studio/
  SKILL.md            entry point
  references/         setup, research, write, schedule
  scripts/studio.py   helper and local web server (Python 3 standard library)
  assets/             workspace templates and the UI
```

The workspace is plain JSON and Markdown, so it is easy to back up, read, or edit by hand. `studio.py sql "…"` queries a SQLite copy of it.

## Develop

```sh
python3 -m unittest discover tests
```
