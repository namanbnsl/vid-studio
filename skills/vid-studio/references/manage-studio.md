# Ongoing studio management

Management requests don't advance content projects. Read configuration/state and selected preferences; users operate conversationally, not through a mandatory JSON editor.

- Discover sources/topics/search queries using research interests, source tastes, freshness, geography and ranking criteria. Show reasons and actual source leads. Suggestions remain disabled until approved.
- Add a stable source/topic ID, URL/feed/query, purpose, profile, watch condition, cadence/timezone and enabled state. Ask only for material missing scope. A complete explicit command authorizes the exact local addition.
- Edit query/filter/cadence/profile with a concrete diff and record authorization. Don't invent connections/schedules.
- Pause/resume toggles enabled state and reconciles host tasks within approved scope. Distinguish one monitor from the shared schedule; preserve evidence/checkpoints.
- Remove defaults to disable/archive, retaining findings/projects/evidence. Removing a monitor doesn't delete research/videos.
- Inbox shows new signals, relevance/novelty reasons, source dates/links, duplicates, ignored candidates and pending decisions. Ranking follows the selected profile.
- Select/research creates a project direction for topic review. Research-only can finish at its research gate.
- Create/clone/edit/display/rename/set-default profiles using profiles.md. Keep stable IDs on name changes. Retire referenced profiles rather than deleting them; resolve routing references before replacement.
- Schedules show cadence/timezone/scope and real host IDs; reconcile create/edit/pause/resume and save confirmation. If no scheduler exists, offer a reviewed alternative.

## Records

Sources (sources array in monitoring/sources.json): id, name, kind (website/feed/search/alert/import), url/query, purpose, enabled, archived, cadence, timezone, profile_id, topic_ids, watch (include/exclude terms, section/change/freshness conditions), optional limits.

Topics (topics array in monitoring/topics.json): id, title, keywords, exclusions, mode (one_off/recurring), enabled, archived, cadence/timezone, source_ids, profile_id, preferences and novelty/episode criteria.

Specific cadence overrides studio monitoring defaults; monitoring never implies publishing. Approved schedule/config files exclude mutable checkpoints (state.json). Candidate decisions belong in inbox records. Configuration changes/authorization go in settings/changes.json.

## Recurring collection

Collect only enabled/nonarchived records in approved scope, respecting filters, policy and limits. Deduplicate and compare prior findings; save relevance reasons, dates and evidence. No changes can yield “no new relevant findings” without producing content. A failed retrieval doesn't advance source success checkpoints.

Prefer host tasks that read live approved configuration. If instructions embed changed filters or scope, update the actual task and save confirmation. Cadence changes require host reconciliation, not just local edits.

Collection can continue while a project waits for approval, but cannot rewrite reviewed artifacts, auto-select episodes, learn tastes silently or publish. External notifications require authorization.
