---
name: vid-studio
description: Research studio for explainer-video channels, kept in local files with a web UI. Use for anything about it — setting up a channel, adding or changing topics and sources, "research now" or scheduled research runs, finding news for the channel's topics, writing or rewriting a script's draft (video script, WhatsApp post, research notes), opening the studio UI, or "what's new".
---

# Vid Studio

The studio holds one or more **channels** (a YouTube channel, Instagram account, WhatsApp channel, and so on). Each channel has:
- **Topics:** what the channel makes videos about. Each one is a name plus a description that guides relevance.
- **Sources:** websites every research run *must* check. You suggest new ones; the user approves.
- **Findings:** new developments that research found on your sources and across the web. Each finding is linked to its topics and to the exact pages it came from.
- **Scripts:** linked to findings (news), topics (explainers), or both. Each holds a video script, a WhatsApp post, and research notes.

The user works in the studio UI. You do the thinking work: research runs and drafts.

The helper is `python3 <this-skill-dir>/scripts/studio.py <command>`, and `--help` lists its commands. The studio folder is `$VID_STUDIO_HOME`, else `~/vid-studio`; each channel lives in `channels/<id>/` inside it. If the prompt names a workspace ("Workspace: /path"), pass `--workspace /path` on every command.

**Which channel.** Prompts from the studio name the channel ("…for the channel \"Pipe Gyaan\""). Pass `--channel "Pipe Gyaan"` (a name or an ID) on every command. If there's only one channel, or `$VID_STUDIO_CHANNEL` is set, you can leave it out. If several exist and the request doesn't say which, run `studio.py channels` and ask.

## Route the request

Start with `studio.py status`.

| The user wants… | Do |
|---|---|
| No channel yet, a new channel, or no topics | [setup.md](references/setup.md) |
| "Research now", a scheduled run, or "what's new" | [research.md](references/research.md) |
| "Write the draft for the script …", or rewrite or edit a script | [write.md](references/write.md) |
| A daily schedule | [schedule.md](references/schedule.md) |
| Open, show, or see the studio | Run `studio.py serve --background` and share the printed link (one server serves every channel) |
| Add, change, or remove topics or sources | Use `studio.py add-topic` / `add-source` (approved) / `suggest-source` (for the user to approve), or edit `topics.json` / `sources.json` |
| A question across the data | Read the channel's JSON files directly |

## Rules

- **Files are the state.** Read them fresh; the user also edits them through the UI. Never overwrite text the user wrote without being asked.
- **Only cite pages you actually opened.** Your own knowledge can point you at where to look, but it is never a source.
- **Never invent anything:** search results, numbers, quotes, or a running schedule. If a tool you need is missing, say so.
- **Language.** `studio.json` → `language` sets the language of the video script (`script.md`) and the WhatsApp post (`post.md`) only. Everything else stays in English: findings, research notes, topics, source notes, and your replies.
  - `English`: plain English.
  - `Hindi`: Hindi in Devanagari, never romanized. Common English technical terms and brand names may stay in English.
  - `Hinglish`: natural Hindi + English mixing, the way the audience talks. Hindi words in Devanagari; English words, brands, units, and numbers in Latin script. For example: "HDPE pipe-grade resin के rates 8–10 October को बढ़े". Not every sentence needs Hindi in it; keep technical terms in English where that's what people say.
  - Never write Hindi in Latin letters ("ke rates badhe").
- **Scheduled or unattended runs:** don't ask questions; do the work and report.
- **End with the studio link** whenever you changed something, so the user can review it.
