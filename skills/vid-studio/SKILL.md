---
name: vid-studio
description: Research and production studio for explainer videos, kept in local files with a web UI. Use for anything about it — setting up a project or channel, adding or changing topics and sources, "research now" or scheduled research runs, finding news for the project's topics, researching a story, writing or revising a script for a channel (including addressing comments), opening the studio UI, or "what's new".
---

# Vid Studio

The studio holds one or more **projects**: each is a subject area the user researches and makes videos about. Each project has:
- **Topics:** what the project makes videos about. Each one is a name plus a description that guides relevance.
- **Sources:** websites every research run *must* check. You suggest new ones; the user approves.
- **Findings:** new developments that research found on your sources and across the web. Each finding is linked to its topics and to the exact pages it came from.
- **Stories:** an angle for a video, linked to findings (news), topics (explainers), or both. Each holds research notes, researched once.

That's the research half. In the production half, a story becomes **scripts**: one per **channel** the user sends it to. Channels (a YouTube channel, Instagram account, WhatsApp channel, and so on) are shared by every project and live in `channels.json` at the studio root, with per-channel settings in `channels/<id>/`:
- **Voice** (`voice.json`): length, pace, persona, tone, hook styles, rules, and example scripts the user loves. Together with the channel's language, kind (`video` script or text `post`), and format (beat structure), it shapes every script.
- **Look** (`design.json`, video channels): colors, fonts, motion, captions. Video scripts are written as beats with `Visual:` lines that become animated scenes in this look; the studio previews them live and can export them for rendering.

The user moves scripts through stages (script → ready → published) and comments on passages for you to address.

The user works in three global UI tabs: **Research** (project topics, sources, findings, stories), **Production** (scripts across all projects), and **Channels** (shared destinations and their look/voice). A research story flows into production scripts, each linked to its source project/story and destination channel. Channels and Production do not require a selected research project. You do the thinking work: research runs, story research, and scripts.

The helper is `python3 <this-skill-dir>/scripts/studio.py <command>`, and `--help` lists its commands. The studio folder is `$VID_STUDIO_HOME`, else `~/vid-studio`; each project lives in `projects/<id>/` inside it. If the prompt names a workspace ("Workspace: /path"), pass `--workspace /path` on every command.

**Which project.** Prompts from the studio name the project ("…for the project \"Pipe Gyaan\""). Pass `--project "Pipe Gyaan"` (a name or an ID) on every command. If there's only one project, or `$VID_STUDIO_PROJECT` is set, you can leave it out. If several exist and the request doesn't say which, run `studio.py projects` and ask.

## Route the request

Start with `studio.py status`.

| The user wants… | Do |
|---|---|
| No project yet, a new project, or no topics | [setup.md](references/setup.md) |
| "Research now", "run the scheduled research", or "what's new" | [research.md](references/research.md) |
| "Research the story …" | [story.md](references/story.md) |
| "Write the script(s) …", "revise the script …" (its comments), or edit a script | [write.md](references/write.md) |
| Add or change channels | `studio.py add-channel` (`--kind video\|post`, `--language`, `--platform`, `--format`), or edit `channels.json` |
| "Change the look of the channel …" | [look.md](references/look.md) |
| "Tune the voice of the channel …" | Read `studio.py voice --channel C`, change what was asked (see the voice section of [script-craft.md](references/script-craft.md) for what each setting does), and save with `studio.py voice --channel C --file -`. If they share example scripts, add them to `examples` with a line on what to learn from each. |
| Preview or render a script's video | `studio.py scenes --script S` checks beats and timing ([scenes.md](references/scenes.md)); `studio.py export --script S` writes a HyperFrames project to render |
| Set up, change, or turn off a research schedule (never runs research) | [schedule.md](references/schedule.md) |
| Open, show, or see the studio | Run `studio.py serve --background` and share the printed link (one server serves every project) |
| Add, change, or remove topics or sources | Use `studio.py add-topic` / `add-source` (approved) / `suggest-source` (for the user to approve), or edit `topics.json` / `sources.json` |
| A question across the data | Read the project's JSON files directly |

## Rules

- **Files are the state.** Read them fresh; the user also edits them through the UI. Never overwrite text the user wrote without being asked.
- **Only cite pages you actually opened.** Your own knowledge can point you at where to look, but it is never a source.
- **Never invent anything:** search results, numbers, quotes, or a running schedule. If a tool you need is missing, say so.
- **Language.** A script's channel → `language` sets the language of that script (`script.md`) only. Everything else stays in English: findings, story notes, topics, source notes, and your replies.
  - `English`: plain English.
  - `Hindi`: Hindi in Devanagari, never romanized. Common English technical terms and brand names may stay in English.
  - `Hinglish`: natural Hindi + English mixing, the way the audience talks. Hindi words in Devanagari; English words, brands, units, and numbers in Latin script. For example: "HDPE pipe-grade resin के rates 8–10 October को बढ़े". Not every sentence needs Hindi in it; keep technical terms in English where that's what people say.
  - Never write Hindi in Latin letters ("ke rates badhe").
- **Scheduled or unattended runs:** don't ask questions; do the work and report.
- **End with the studio link** whenever you changed something, so the user can review it.
