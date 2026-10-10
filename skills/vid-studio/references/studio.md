# Set up and manage the studio

## Set up

Ask about the user's purpose and audience first. Then ask about these items in short groups:

- Topics, sources, research depth, and freshness.
- Script and post language, tone, structure, and templates.
- Brand, visuals, motion, voice, and captions.
- Outputs, workspace, tools, services, costs, monitors, cadence, and timezone.

Use supplied examples and templates. Record choices that remain open. Research and monitors can start before video setup.

Show one setup proposal. Include preferences, initial monitors, immediate actions, and tools for later setup. After approval, run the initializer:

```sh
python3 <skill-directory>/scripts/init_workspace.py --workspace <path>
```

Enter the approved choices. Configure only the selected tools. Show the completed setup for approval before activation. Keep existing agent configuration.

The initializer keeps existing files. It does not install tools, create schedules, or approve work.

## Workspace files

- studio.json contains shared preferences, tools, and permissions.
- brand/frame.md contains video design instructions. Add reference files and templates as necessary.
- monitoring/sources.json and topics.json contain monitor definitions.
- monitoring/state.json contains collection checkpoints. inbox/ contains findings.
- STATUS.md contains decisions, active projects, and the next action.
- projects/<id>/ contains project settings, evidence, scripts, production files, and approval notes.

Create only necessary files. Record decisions in STATUS.md. Keep earlier versions of reviewed files. Keep existing workspace conventions. Do not migrate an existing workspace without approval.

## Preferences

Start with the supplied defaults. Add fields only when necessary. Use text instructions for detailed preferences. Preserve custom fields.

A user template takes precedence over example content. A script can have an exact structure without a hook. Research, posts, design, motion, audio, captions, and review format are editable.

A precise user instruction authorizes that exact local edit. If the scope is unclear, ask which project, profile, or default to change. Keep project feedback local unless the user requests a persistent rule. Get approval before you activate suggested preferences or sources.

For multiple brands or audiences, create optional profiles/<id>.json files. Each profile contains id and preferences. Select the profile on a project or monitor.

The helper merges defaults, the selected profile, topic preferences, and project overrides, in that order. Nested objects merge. Lists replace earlier lists. An empty list or null clears a value. Existing profiles can use extends for inheritance. Do not add inheritance without a useful purpose.

Create project.json from the template. Then resolve the project preferences:

```sh
python3 <skill-directory>/scripts/resolve_preferences.py --workspace <path> --project <id>
```

Save the report as preferences.json. Copy applicable templates and brand references into context/. Include these files in topic review.

When you resume reviewed work, use --project <id> --frozen. Read approvals.md separately. The helper reads saved settings. It does not enforce approval.

Changes to studio preferences apply to future work. Apply them to an active project only when requested. Show the differences. Save a new settings copy. Keep the reviewed copy. After approval, update preferences_path. Reopen the earliest affected stage and later stages.

Script style affects editorial review. Visual style affects storyboard review. Topic or output scope affects topic review. Earlier approved stages keep their original settings. Reduced service permissions or cost limits apply immediately to all projects.

## Monitors and inbox

Find source and topic suggestions from the user's research preferences. Include reasons and actual source links. Add, edit, pause, resume, or archive monitors through conversation. Keep stable IDs. Keep findings when you archive a monitor.

Source records contain id, name, URL or query, kind, and enabled state. Optional fields include profile_id, filters, cadence, and timezone. Topic records contain id, title, mode, source_ids, and enabled state. Optional fields include profile_id, preferences, cadence, and timezone. Add detailed watch conditions only when necessary.

Collect from enabled records that are not archived. Stay within the approved scope. Save URLs, dates, evidence, and relevance notes locally. Remove duplicate findings. If retrieval fails, do not advance the success checkpoint.

Show findings in order of relevance and novelty. Let the user select the next topic. If no evidence is new, report that result. Do not start production automatically.

Use available feeds, search tools, and browser tools. Alerts and Trends are optional inputs. Do not invent integration status or trend data.

Use the host scheduler only within approved scope. Save the actual task ID and confirmation. Apply cadence and pause changes to the actual task. A saved cadence is not a running schedule. If no scheduler is available, support manual collection.

Scheduled instructions name the workspace and read the current monitors and permissions. The agent collects findings, removes duplicates, and updates STATUS.md. The agent stops at project approval stages. Collection can continue while a project waits for approval. It cannot change reviewed content or publish without authorization.
