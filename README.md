# Vid Studio

A skill pack for automating explainer-video research with any AI agent that supports [skills](https://skills.sh/), such as Claude Code, Codex, and others. It is a single skill, `vid-studio`, so you never have to remember which one to call. Ask in plain language and it routes itself.

All data stays local in a workspace folder (default `~/vid-studio`).

## Install

```sh
npx skills add namanbnsl/vid-studio
```

## Use

> Use vid-studio.

The first run sets up your profile, proposes sources and topics, and offers a daily schedule. After that, ask for anything:

- "Use vid-studio — what's new today?"
- "Use vid-studio to monitor RBI press releases and Google News for UPI."
- "Use vid-studio to research how India's semiconductor subsidies work."
- "Use vid-studio — make the hook punchier and approve the script."
- "Use vid-studio — run the daily routine." (this is what the scheduler sends)

## What it does

**Research workspace**

1. **Sources.** Websites (RSS auto-discovered), Google News searches, Google Alerts RSS feeds, and Google Trends by country. A scan pulls new items into a dated inbox and skips duplicates.
2. **Topics.** Found from the inbox, Trends, and your interests. Each topic is `once` (one explainer) or `daily` (checked every day; a video is made only when there's real news).
3. **Research.** Plan the subtopics, search, go upstream to primary sources, and save every cited source locally. Build a claim ledger with exact quotes. Cross-check the key facts, then write a cited brief with chart data and asset ideas.
4. **Write.** A WhatsApp post and a video script in your standard structure. The script includes a visual plan for each beat (charts, real assets, graphics), with every fact tagged to a verified claim.
5. **Review.** You edit and approve the script. `studio.py check` blocks review while citations are unsupported.

**Explore.** Say "Use vid-studio, show me my studio" and the agent replies with a link (`http://localhost:8765`). The dashboard shows:
- the pipeline and an inbox search
- topics, with their leads and run history
- source health
- for each project: the brief, the script with claim chips (hover to see the fact, click to see its sources), a WhatsApp preview, the claim ledger, sources with local evidence, and chart data

It works in light and dark mode. You can also open `~/vid-studio/ui/index.html` directly as a snapshot.

**Storage.** JSON and Markdown files are the source of truth, so any agent or person can read and edit them. `studio.db` is a SQLite index that is rebuilt automatically, so you can query it: `studio.py sql "SELECT status, count(*) FROM claims GROUP BY status"`.

**Video workspace.** Not built yet. The approved `script.md` and its `data/` folder are the hand-off.

## Files

```
skills/vid-studio/
  SKILL.md              entry point and router
  references/           setup, discover, research, write, schedule playbooks
  scripts/studio.py     workspace helper (Python 3 stdlib): init, status, add-source, add-topic,
                        scan, lead, triaged, new-project, no-news, snapshot, check, stage,
                        ui, serve, sql
  assets/               workspace, project, and explorer (ui/index.html) templates
```

Scheduling: [schedule.md](skills/vid-studio/references/schedule.md) covers cron or launchd running a headless agent locally, host-app scheduled tasks, and why cloud schedulers (ChatGPT Tasks and similar) can't write to your local workspace.

## Develop

```sh
python3 -m unittest discover tests
```
