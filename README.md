# Vid Studio

A skill for running research for explainer videos with any AI agent that supports [skills](https://skills.sh/), such as Claude, ChatGPT, or Codex. All data stays in a local folder, and you work in a small web UI.

```sh
npx skills add namanbnsl/vid-studio
```

## How it works

The studio has two halves.

**Research** happens in **projects** (each one a subject area, such as plumbing products or Indian tech news), and you switch between them in the UI. Each project has:

- **Topics:** what the project makes videos about. Each one is a name plus a description of what matters.
- **Sources:** websites every research run must check. Research also suggests new ones for you to approve.
- **Findings:** short items on new developments, each linked to its topics and to the pages it came from. Dismiss what you don't need.
- **Stories:** an angle for a video, built from findings, topics, or both, with research notes.

**Production** turns a story into **scripts**, one per **channel** you send it to. Channels (each YouTube channel, Instagram account, or WhatsApp channel) are shared by every project and set each script's language and format, so one story can become an English Short, a Hinglish Reel, and a Hindi WhatsApp post. Scripts move through stages (script, ready, published), and you can comment on any passage for your agent to address.

The steps that need an AI each have a button that copies a prompt. Paste it into Claude or ChatGPT, and the results show up in the UI:

- **Research now:** your agent researches every topic and adds findings.
- **Research story:** your agent researches a story's findings and topics in depth and writes its notes.
- **Send to production**, then **Write draft:** your agent writes each channel's script from the story's notes. With open comments, the button becomes **Revise**, and your agent works through them in order.

To research on a schedule, click the schedule link under **Research now**, pick the days and times, and paste the copied prompt into your agent. It creates the scheduled task.

## Start

> Use vid-studio to set up my project.

Your agent creates the studio (`~/vid-studio` by default, one folder per project in `projects/`), proposes topics and sources, and opens the studio at `http://localhost:8765`. Later, "Use vid-studio, open the studio" brings it back.

## Files

```
skills/vid-studio/
  SKILL.md            entry point
  references/         setup, research, story, write, schedule
  scripts/studio.py   helper and local web server (Python 3 standard library)
  assets/             workspace templates and the UI
```

The workspace is plain JSON and Markdown, so it is easy to back up, read, or edit by hand.

## Develop

```sh
python3 dev.py demo              # throwaway studio full of sample data, opened in your browser
python3 dev.py sandbox --seed    # test project at ../vid-studio-sandbox, with the skill linked (not copied)
python3 dev.py try setup         # run Claude Code headlessly in the sandbox (setup, research, story, draft, status, or any prompt)
python3 dev.py try research --agent codex
python3 dev.py reset --yes       # wipe the sandbox's studio data
python3 -m unittest discover tests
```

The sandbox links the skill into `.claude/skills` and `.agents/skills`, so edits to this repo apply on the next prompt with no reinstall. Its studio data lives in the sandbox, so your real `~/vid-studio` is never touched. For interactive testing: `cd ../vid-studio-sandbox && claude`.
