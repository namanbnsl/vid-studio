---
name: vid-studio
description: One entry point for an explainer-video research studio. Use for anything about it — setting up the studio, opening the studio dashboard/explorer UI, querying studio data, finding websites/feeds/Google Alerts/Google Trends to monitor, discovering or managing topics (one-time or daily), scanning sources, researching a topic with sourced and verified claims, writing WhatsApp posts and video scripts, reviewing/editing/approving scripts, scheduling the daily routine, or "what's next" / "run the daily routine". All data stays in a local workspace.
---

# Vid Studio

The user calls this one skill for everything. Work out what they want, load the matching playbook, and carry the work forward without making them name steps.

The helper `scripts/studio.py` (Python 3 standard library) owns the workspace files. Run it as `python3 <this-skill-dir>/scripts/studio.py <command>`. The workspace is `$VID_STUDIO_HOME`, else `~/vid-studio`; pass `--workspace PATH` if the user names another one. Every command prints its result; `--help` lists options.

## Always start here

Run `studio.py status`. It reports setup gaps, sources, topics, the inbox, projects by stage, and a list of next actions. Use it to resume any session.

Then route:

| The user wants… | Playbook |
|---|---|
| First run, or setup is incomplete | [setup.md](references/setup.md) |
| Find or manage websites, feeds, alerts, trends | [discover.md](references/discover.md#sources) |
| Find, add, approve, or pause topics; change once/daily | [discover.md](references/discover.md#topics) |
| Check sources for news, review the inbox | [discover.md](references/discover.md#scan) |
| Research a topic, or continue a project | [research.md](references/research.md) |
| WhatsApp post, script, edits, approval | [write.md](references/write.md) |
| Daily routine, scheduled run, or automation setup | [schedule.md](references/schedule.md) |
| Show, open, browse, or explore the data | [Explorer](#explorer) below |
| A question across the data ("which claims are disputed?") | `studio.py sql "SELECT …"` (no query prints the schema) |
| "What's next?", "continue", or a bare invocation | Do the first actionable item from `status` |

If setup is incomplete, finish onboarding first. Exception: if the user asks to research one specific topic right away, do it with defaults and finish setup afterwards.

## Explorer

The explorer is a local web dashboard. It covers the overview and pipeline, the inbox, topics, sources, and digests. Each project shows its brief, script, WhatsApp post preview, claims, sources with their local evidence, and chart data.

- Run `studio.py serve --background` and give the user the printed `http://localhost:…` link as a clickable Markdown link. The page always shows the latest files, and the command reuses a running server. Stop it with `serve --stop`.
- If the server cannot start, run `studio.py ui` and share the `file://` link. It is a snapshot, rebuilt automatically after every `studio.py` command that changes data.
- After you edit project files directly, run `studio.py ui` so the snapshot and `studio.db` catch up.
- End sessions that changed data with the explorer link.

Storage: JSON and Markdown files are the source of truth, so edit those. `studio.db` is a derived SQLite index that is rebuilt every time; never write to it.

## How to behave

- **Move the work forward.** After each step, do the next one in the same turn unless a review gate in `studio.json` → `review` says to stop. By default the gates are approving new topics and approving the final script.
- **When nobody is watching** (scheduled or headless runs), never stop to ask a question. Do every step that needs no approval. Leave gated items waiting. Write a digest of what happened (see schedule.md).
- **Files are the memory.** Read state from the workspace and write results back. Do not rely on chat history. The user may edit any file by hand; reread files before changing them.
- **Evidence over recall.** Only sources you actually opened can support a claim. Use your own knowledge to find leads and plan, never as a citation. Save every cited source locally with `studio.py snapshot`.
- **Be honest about tools.** Use whatever search, browsing, and subagent tools the host offers. If a capability is missing (no web access, no scheduler), say so and use the fallback in the playbook. Never invent search results, trends data, or a running schedule.
- **Scope.** This skill covers research through an approved script and post. It does not render video, send messages, or publish.
- **Write plainly.** Status updates should be short: what you did, what is waiting for the user, and what comes next.
