---
name: vid-studio
description: Research studio for an explainer-video channel, kept in local files with a web UI. Use for anything about it — setting up the channel, adding or changing topics and sources, "research now" or scheduled research runs, finding news for the channel's topics, writing or rewriting a script's draft (video script, WhatsApp post, research notes), opening the studio UI, or "what's new".
---

# Vid Studio

One channel per workspace. The workspace holds:
- **Topics:** what the channel makes videos about. Each one is a name plus a description that guides relevance.
- **Sources:** websites every research run *must* check. You suggest new ones; the user approves.
- **Findings:** new developments that research found on your sources and across the web. Each finding is linked to its topics and to the exact pages it came from.
- **Scripts:** linked to findings (news), topics (explainers), or both. Each holds a video script, a WhatsApp post, and research notes.

The user works in the studio UI. You do the thinking work: research runs and drafts.

The helper is `python3 <this-skill-dir>/scripts/studio.py <command>`, and `--help` lists its commands. The workspace is `$VID_STUDIO_HOME`, else `~/vid-studio`. If the prompt names a workspace ("Workspace: /path"), pass `--workspace /path` on every command.

## Route the request

Start with `studio.py status`.

| The user wants… | Do |
|---|---|
| No workspace yet, or no topics | [setup.md](references/setup.md) |
| "Research now", a scheduled run, or "what's new" | [research.md](references/research.md) |
| "Write the draft for the script …", or rewrite or edit a script | [write.md](references/write.md) |
| A daily schedule | [schedule.md](references/schedule.md) |
| Open, show, or see the studio | Run `studio.py serve --background` and share the printed link |
| Add, change, or remove topics or sources | Use `studio.py add-topic` / `add-source` (approved) / `suggest-source` (for the user to approve), or edit `topics.json` / `sources.json` |
| A question across the data | `studio.py sql "SELECT …"` (with no query, it prints the tables) |

## Rules

- **Files are the state.** Read them fresh; the user also edits them through the UI. Never overwrite text the user wrote without being asked.
- **Only cite pages you actually opened.** Your own knowledge can point you at where to look, but it is never a source.
- **Never invent anything:** search results, numbers, quotes, or a running schedule. If a tool you need is missing, say so.
- **Scheduled or unattended runs:** don't ask questions; do the work and report.
- **End with the studio link** whenever you changed something, so the user can review it.
