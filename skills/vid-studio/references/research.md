# Research

You decide how to research: what to search, how deep to go, which sources to trust, when you're done. This file only defines what a finished project must contain, so the tools, the explorer, and the scriptwriting step can rely on it.

## Goal

A `brief.md` a scriptwriter can trust. It answers the question the video is about, for this audience (`studio.json`). Every fact in it is traced to a source you actually read and saved locally. What is contested or unknown is stated plainly instead of being smoothed over.

## Starting

- Continue an existing project from its `stage` in `project.json`.
- Otherwise run `studio.py new-project --topic ID`, or `--title "..."` for an ad-hoc request. The new project carries the topic's `leads`, `queries`, and `previous_projects`.
- **Daily topics:** first decide whether anything meaningful happened since the topic's `last_run`; the previous project's brief is the baseline. If nothing did, run `studio.py no-news --topic ID --note "what you checked"` and stop. Restating known facts is not news.

Use `plan.md` for whatever working notes help you: the question, the angle, open questions, scope. If `review.plan` in `studio.json` is true, show the plan and wait before researching. Then run `studio.py stage ID researching`.

## Contract

These rules are what make the output trustworthy and machine-checkable. Everything else is up to you.

**Sources.** Capture every source you cite with `studio.py snapshot PROJECT URL --type primary|data|secondary|analysis|opinion`. If the fetch fails or comes back thin, read the page with your own tools, save the relevant text to a file, and pass `--text-file FILE --title T --publisher P --published DATE`. Capture the original article, never a news.google.com redirect. Never cite sites in `research.blocked_sources`.

**Claims.** Put each factual claim in `claims.json`:

```json
{"id": "C1", "text": "…one checkable fact, with its number, unit, date, and place…",
 "sources": ["S3", "S7"], "status": "verified", "quote": "…exact supporting text from the evidence…", "note": ""}
```

Statuses mean the following. `studio.py check` enforces the first:

| Status | Meaning |
|---|---|
| `verified` | Backed by a primary or data source, or by independent publishers on two or more domains. Syndicated copies of one wire story count as one source. |
| `single-source` | One credible source. The script must attribute it. |
| `disputed` | Credible sources disagree. `note` gives both sides. |
| `unverified` | Not confirmed. It can appear in the brief as an open question, never in the script. |

Add any extra fields you find useful (`subtopic`, `confidence`, and so on).

**Model knowledge** can guide where you look. It is never a source.

**Chart data** goes in `data/<name>.csv`, with a source-ID column. If you transform values, note how in `data/<name>.md`. Never invent missing values.

**Brief.** `brief.md` cites claim IDs inline, like `[C1]` or `[C2, C5]`. It should leave the scriptwriter with:
- the answer
- the key numbers
- what's new (daily topics)
- what's disputed or unknown
- visual opportunities: charts with their data files, and real assets (official images, documents, footage) with their URLs and any usage notes
- a recommended angle and takeaway

Structure it however best serves the topic. The template is only a starting point.

## Finishing

1. Run `studio.py check PROJECT`. Fix every ERROR. Fix each WARN or knowingly accept it.
2. If `review.brief` is true, run `studio.py stage ID brief-review`, summarise the brief for the user, and wait.
3. Otherwise run `studio.py stage ID writing` and continue with [write.md](write.md).

If facts change later, update the sources, claims, and brief, rerun `check`, and fix the script lines they affect.
