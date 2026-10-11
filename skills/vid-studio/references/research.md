# Research

Goal: a project folder whose `brief.md` a scriptwriter can trust. Every fact in it is traced to a source saved locally.

Project files:
- `plan.md`
- `sources.json` (registry)
- `evidence/` (saved source text)
- `claims.json` (claim ledger)
- `data/` (chart data)
- `brief.md`
- `project.json` (stage and history)

## 0. Start or resume

- If a project already exists, continue from its `stage`.
- For a topic, run `studio.py new-project --topic ID`.
- For an ad-hoc request, run `studio.py new-project --title "..."` and add `--angle` if the user gave one.

**Daily topics:** first decide whether there is news. Read the topic's `leads`. Run 2-3 searches restricted to the period since `last_run`. Read the latest previous brief as a baseline. Is there a meaningful development the audience should hear about: a new decision, data release, number, or turn of events? If not, run `studio.py no-news --topic ID --note "what you checked"` and stop. A repeat of known facts is not news. Only create a project when there is news. The project's `previous_projects` lists earlier projects to compare against.

## 1. Plan (`stage: planning`)

Fill `plan.md`:

- **One question** the video answers.
- **Angle** for this audience. For daily topics, add "what changed since <previous project>".
- **3-6 subtopics.** Each has 2-4 concrete questions and the best source types for it. A useful default set:
  1. What happened / what is it
  2. Background and why now
  3. How it works (the mechanism)
  4. The numbers
  5. Who is affected, and how
  6. Counter-arguments and uncertainty
- **Scope:** date window from `research.freshness_days`, and what is out of scope.
- **Data needed** for at least one chart.

If `review.plan` is true, show the plan and wait. Otherwise set the stage with `studio.py stage ID researching` and continue.

## 2. Collect sources (`stage: researching`)

Work subtopic by subtopic. If the host supports parallel subagents, give each one a subtopic, the project path, and this file. Each subagent captures its own sources and returns claims. Merge their claims into `claims.json` yourself, renumbering if needed.

For each subtopic:

1. **Search broadly.** Run several queries per question with different wording. Include official names, document titles, and operators like `site:gov.in`, `filetype:pdf`, or `site:sec.gov`. Search in the local language when the story is local. Start from the project's `leads` and `queries`.
2. **Go upstream.** When an article cites a report, dataset, filing, court order, or press release, find and capture that original document. Mark it `--type primary`. Datasets and statistical tables get `--type data`.
3. **Capture what you will cite.** Run `studio.py snapshot PROJECT URL --type TYPE`. If the fetch fails or returns very little text (paywalls, script-heavy pages, PDFs you read elsewhere), open the page with your own browsing tool. Save the relevant text to a temp file, then run `snapshot ... --text-file FILE --title T --publisher P --published DATE`. Never capture a `news.google.com` redirect; open it and capture the real article.
4. **Respect settings.** Never cite `research.blocked_sources`. Prefer `research.trusted_sources`. Skip content farms and AI-generated SEO pages.

Target source counts by `research.depth`: quick 5-8, standard 10-15, deep 20+. Every subtopic needs at least two sources.

## 3. Build the claim ledger

Add one record per atomic fact to `claims.json`:

```json
{"id": "C1", "text": "India's UPI processed 18.7 billion transactions in Sept 2026.",
 "subtopic": 4, "sources": ["S3", "S7"], "status": "verified",
 "quote": "…exact supporting sentence from S3…", "note": ""}
```

Rules:
- **One fact per claim**, with its number, unit, date, and geography.
- **`quote`** is the exact supporting text from the evidence file. If you cannot quote it, the source does not support it.
- **Statuses:**
  - `verified` means a primary or data source, or at least two independent publishers.
  - `single-source` means one credible secondary source.
  - `disputed` means credible sources disagree. Put both sides in `note`, with source IDs.
  - `unverified` means a lead you could not confirm. It cannot be used in the script.
- **Independence:** several outlets rewriting one wire story or press release count as one source. Trace them to the origin and cite that instead.
- **Numbers:** use the latest figure and check the date. Confirm units and the base. Crores vs millions, nominal vs real, and YoY vs MoM are common traps. Note rounding. Never compute a figure without saving the calculation (see data below).
- **Do not invent missing values.** Write the gap down instead.

## 4. Cross-check and fill gaps

1. Go through the claims the story depends on: the hook fact, every number, and anything surprising. Try to confirm each from an independent source. Also search for contrary evidence, such as "<claim> criticism", "<claim> false", or the opposing party's statement. Update statuses.
2. List the plan's questions that are still unanswered. Do at least one more targeted search round for them.
3. Record anything that stays unknown in the brief. Leaving it there is better than guessing.

## 5. Chart data

For each proposed chart, save `data/<name>.csv` with a header row. Include columns for value, unit, date or period, and source ID. Note any transformation in a `data/<name>.md`, such as "values converted from crore to billion: ×0.01". Use only captured sources.

## 6. Brief

Fill `brief.md`. Every factual sentence cites claim IDs like `[C1]` or `[C2, C5]`. The brief has these sections:

- **Summary:** 3-5 sentences.
- **What's new:** daily topics only.
- **Findings:** one section per subtopic.
- **Key numbers:** a table.
- **Disputes and uncertainty**, stated honestly.
- **Visual opportunities:**
  - charts with their data files
  - real assets (official photos, document screenshots, maps, product images, footage) with the source URL and any licence or credit note
  - diagrams worth drawing
- **Recommended angle and takeaway.**

## 7. Check and hand off

Run `studio.py check PROJECT` and fix every ERROR. Then decide each WARN: fix it or accept it consciously.

If `review.brief` is true, run `studio.py stage ID brief-review`, show the summary, key numbers, and open questions, and wait. Otherwise run `studio.py stage ID writing` and continue with [write.md](write.md).

## If the user changes facts or scope later

Add or adjust sources and claims, rerun `check`, and update the brief. If the script already exists, update the affected lines too (see write.md).
