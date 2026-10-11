# Vid Studio

A skill for running an explainer-video channel's research with any AI agent that supports [skills](https://skills.sh/), such as Claude, ChatGPT, or Codex. All data stays in a local folder, and you work in a small web UI.

```sh
npx skills add namanbnsl/vid-studio
```

## How it works

The studio holds your **channels** (each YouTube channel, Instagram account, or WhatsApp channel), and you switch between them in the UI. Each channel has four parts:

- **Topics:** what the channel makes videos about. Each one is a name plus a description of what matters.
- **Sources:** websites every research run must check. Research also suggests new ones for you to approve.
- **Findings:** short items on new developments, each linked to its topics and to the pages it came from. Dismiss what you don't need.
- **Scripts:** built from findings, topics, or both. Each holds the video script, a WhatsApp post, and research notes.

You manage topics, sources, and scripts in the UI. The two steps that need an AI each have a button:

- **Research now** copies a prompt. Paste it into Claude or ChatGPT; your agent researches every topic and the new findings show up in the UI.
- **Write draft** (in a script) copies a prompt; your agent researches the attached findings in depth and writes the script, the post, and research notes.

To research on a schedule, click the schedule link under **Research now**, pick the days and times, and paste the copied prompt into your agent. It creates the scheduled task.

## Start

> Use vid-studio to set up my channel.

Your agent creates the studio (`~/vid-studio` by default, one folder per channel in `channels/`), proposes topics and sources, and opens the studio at `http://localhost:8765`. Later, "Use vid-studio, open the studio" brings it back.

## Files

```
skills/vid-studio/
  SKILL.md            entry point
  references/         setup, research, write, schedule
  scripts/studio.py   helper and local web server (Python 3 standard library)
  assets/             workspace templates and the UI
```

The workspace is plain JSON and Markdown, so it is easy to back up, read, or edit by hand.

## Develop

```sh
python3 dev.py demo              # throwaway studio full of sample data, opened in your browser
python3 dev.py sandbox --seed    # test project at ../vid-studio-sandbox, with the skill linked (not copied)
python3 dev.py try setup         # run Claude Code headlessly in the sandbox (setup, research, draft, status, or any prompt)
python3 dev.py try research --agent codex
python3 dev.py reset --yes       # wipe the sandbox's studio data
python3 -m unittest discover tests
```

The sandbox links the skill into `.claude/skills` and `.agents/skills`, so edits to this repo apply on the next prompt with no reinstall. Its studio data lives in the sandbox, so your real `~/vid-studio` is never touched. For interactive testing: `cd ../vid-studio-sandbox && claude`.
