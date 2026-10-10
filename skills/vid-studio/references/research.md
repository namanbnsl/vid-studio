# Monitoring and research

## Source and topic management

Use [manage-studio.md](manage-studio.md) for conversational discovery/add/edit/pause/archive actions and [profiles.md](profiles.md) for research tastes. Apply selected interests/exclusions, source priorities, geography, freshness, depth, novelty and ranking rules. Suggestions remain proposals; avoid substituting the agent's own editorial taste.

`monitoring/sources.json` contains a sources array. Each source has id, name, url, kind (website/feed/search/alert), rationale, cadence, and enabled. `monitoring/topics.json` contains a topics array with id, title, keywords, mode (one_off/recurring), cadence, and source_ids. These files are approved configuration; do not store run checkpoints in them.

Store mutable checkpoints in `monitoring/state.json`, keyed by source/topic ID: last_attempt_at, last_success_at, last_researched_at, previous_project_ids, and deduplication keys. Normal collection updates state/inbox/status without changing approved configuration hashes. Changing cadence, source lists, keywords or scope still requires configuration approval.

A precise user command authorizes its exact local source/topic change; propose ambiguous or agent-discovered changes for approval before enabling them. An approved setup list counts as approval of that initial list. Record subsequent configuration approvals in a settings/changes.json with exact changed files and hashes. Config approval does not approve candidate topics or research.

Use feeds and available search tools where practical; use browser retrieval for sites that need it. Google Alerts/Trends are optional inputs, not assumed installed integrations. If unavailable, propose manual alert/feed import or ordinary search; do not fabricate trends or create accounts without authorization.

Save signals with URL, retrieved_at, publication date when available, short relevance note, and a deduplication key. Track successful checks individually; a failed fetch must not advance that source's success checkpoint. Recurring research compares against previous briefs and identifies what changed. No meaningful new evidence can yield a “no new episode recommended” review report.

## Topic selection gate

Create the draft project using assets/project/project.json. Resolve preferences with the helper, save preferences.json and copied context references, and include the selected profile/overrides/deliverables in topic review.

Deliver `01-topic/topic.md`: candidate topic, audience, angle, timeliness, one-off/recurring mode, likely value, and initial source leads. Offer a few alternatives only when needed. Await approval of the chosen topic and angle.

## Research plan gate

Read the approved project preference snapshot. Respect its research interests, angle, source priorities, exclusions, freshness, depth, brief format and time budget.

Deliver `02-plan/research-plan.md`: central question, subquestions, scope exclusions, primary-source targets, disputed points, time window, expected data/charts, and research limits. Await approval before collecting the full research package.

## Research brief gate

For numerical evidence, follow [data-media.md](data-media.md): preserve original and derived datasets locally, with source metadata and reproducible transformations.

Research with the approved plan and available browsing tools. Prefer original publications, first-party data, and authoritative sources; seek corroboration for consequential or disputed statements. Distinguish evidence, interpretation, and unknowns. Save enough retrieved evidence locally to support handoff: URL, publisher/title, dates, relevant excerpts or permitted snapshots, and extraction notes. Respect access and usage restrictions; a link alone is not a local evidence record.

`03-research/claims.json` contains claims with id, text, source_ids, supporting excerpts, as_of, status (supported/disputed/unverified), caveats, and optional data_path. Store corresponding source metadata in `03-research/sources/`. Cite claim IDs in the brief. Document contradictory findings, inaccessible sources, date sensitivity, and excluded unsupported claims. No second-model review is required.

Deliver the brief, claim ledger, sources, and proposed story takeaway. Await approval before writing publishable content. For a research-only scope, this approval completes the requested deliverable; do not generate posts/scripts/videos automatically. If research changes the approved angle materially, return to topic/plan review.
