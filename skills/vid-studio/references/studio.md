# Set up the research studio

Complete this sequence on the first invocation. Prepare the next setup proposal after each approval. Do not require a separate request for each task.

## 1. Onboard

Ask the user's name and preferred studio name. Ask about audience, languages, topic interests, and research purpose. Then ask about taste, script examples, branding, and post format.

Discuss preferred sources, exclusions, depth, freshness, tone, and exact script structure. Ask about available tools, permitted external processing, costs, and timezone. Use short groups of questions. Leave nonessential choices open.

Define a reusable content theme and structure from the answers. Include title style, script sections, WhatsApp format, visual approach, and chart preferences. Use supplied examples and templates. A hook and CTA are optional.

Show the preferences for approval. Do not configure video tools or request production assets.

After approval, initialize missing files:

```sh
python3 <skill-directory>/scripts/init_workspace.py --workspace <path>
```

Fill studio.json with approved choices. Keep existing files and agent configuration. Record completed onboarding in STATUS.md. The initializer does not approve setup or create schedules.

## 2. Find websites

Use the approved research interests to find relevant websites, feeds, and primary sources. Use available search, browser, and LLM tools. Use Google Alerts as an optional discovery input.

Retrieve actual source pages. An LLM suggestion is a lead until verified. Propose source URLs, purpose, coverage, filters, and monitoring method. Explain why each source fits the user.

Add proposed sources as disabled records. After approval, mark them approved for monitor setup. Do not invent an Alerts connection or create an account without authorization. If integration is unavailable, support imported alerts, feeds, or ordinary search.

## 3. Find topics

Find topic suggestions from approved websites and available LLM/search tools. Use Google Trends when accessible and useful. Verify observed trend data before describing a topic as trending.

Propose topics with source leads, audience value, questions, and freshness. Classify each as one-time or daily from context. A fixed explanation is usually one-time. A changing policy or recurring update can need daily research.

Explain each recommendation. Let the user approve, edit, or remove topics before monitor activation. Do not fabricate Trends data. If access fails, report it and use verified source findings.

## 4. Configure monitors

Prepare the schedule proposal from approved sources and topics. Use the user's cadence when specified. Otherwise recommend one-time or daily from the approved context.

A one-time topic has no recurring task. A daily topic needs a time, timezone, scope, and scheduler. Ask only for essential missing values. Show exact schedules and actions for approval.

After approval, configure the available host scheduler. Save actual task IDs and confirmation. Configure approved source filters and topic routing. Keep records disabled until setup completes. Show completed monitors for approval before activation.

If no scheduler is available, report that limitation. Support manual collection. Do not claim that a saved cadence is a running monitor.

Scheduled instructions name the workspace and read current approved monitors. They collect evidence, remove duplicates, update the inbox, and report pending reviews. They do not approve topics, research, or scripts. They stop at the next unapproved stage.

An approved research schedule can resume an already approved topic and plan within their scope. New topics or changed plans need review. Research findings still need approval before script generation.

## Local files

studio.json contains identity, shared preferences, tools, and permissions. STATUS.md contains completed setup steps, decisions, projects, and next actions. monitoring/sources.json and topics.json contain definitions. monitoring/state.json contains checkpoints and confirmed scheduler details. monitoring/inbox/ contains findings.

Source records contain id, name, URL or query, kind, and enabled state. Optional fields include filters, cadence, timezone, and profile_id. Topic records contain id, title, mode, source_ids, and enabled state. Use mode one_off or recurring. For recurring work, record the daily cadence explicitly.

Keep project settings, evidence, scripts, posts, and approvals under projects/<id>/. Create only necessary files. Profiles are optional for multiple brands or audiences. Existing workspace conventions can remain.

## Edit and resume

Add, edit, pause, resume, or archive monitors through conversation. Keep stable IDs and saved evidence. Apply cadence and pause changes to actual scheduler tasks. A failed retrieval does not advance its success checkpoint.

Show findings by relevance and novelty. If nothing is new, report that result. Select the next research topic with the user.

Use text instructions for detailed preferences. Preserve custom fields. User templates take precedence over examples. Project feedback stays local unless the user requests a persistent rule.

For optional profiles, the helper merges defaults, profile, topic preferences, and project overrides. Nested objects merge. Lists replace. Empty lists and null clear values. Existing profiles can use inheritance when useful.

Create project.json from the supplied template. Save resolved preferences as preferences.json. Copy relevant references into context/. Include them in topic review.

```sh
python3 <skill-directory>/scripts/resolve_preferences.py --workspace <path> --project <id>
```

On resume, use --project <id> --frozen. Read approvals.md separately. The helper reads saved settings; it does not enforce approval.

Future preference changes leave reviewed projects unchanged. Apply them to active work only when requested. Show differences and preserve the reviewed copy. Update preferences_path after approval. Reopen the earliest affected stage and later stages.

Reduced service permissions and cost limits apply immediately to all work. Do not add policy registries or unnecessary configuration files.
