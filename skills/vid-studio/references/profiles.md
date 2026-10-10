# Preferences, inheritance and snapshots

studio.json holds operational policy/toolchain and creative/research `defaults`. `default_profile_id` selects profiles/<id>.json. A profile has id, name, revision, status, optional extends (one profile ID), and preferences. Profiles can represent brands, audiences or series.

Fields are extensible. Preserve custom settings/free-form instructions. Keep large templates/references in local files; copy and hash their contents into a project context. The helper resolves JSON, not reference contents or approval state.

## Customization coverage

- Research: interests/exclusions, questions, sources/domain priorities, geography/languages, freshness, depth, subtopic approach, evidence/uncertainty expectations, brief structure, novelty/ranking and time budget.
- Script: exact ordered structure (including no hook), template, tone/persona, complexity/jargon/glossary, language, title/hook rules, examples, duration/pacing, number phrasing, ending and CTA.
- WhatsApp: structure/template, length, tone, emojis, bullets, citations/links and CTA.
- Visual/brand: references, colors, fonts, layout, chart/diagram/real-asset choices, motion intensity/eases/transitions/holds, voice/pronunciation, music/SFX, captions, safe areas, format/fps and variants.
- Monitoring: source queries/feeds/watch conditions, filters, ranking, recurrence/timezone/cadence and profile selection. These live in monitor config.
- Review: presentation/feedback format, notifications and reviewer notes. The current every-stage approval policy is operational policy, not a creative override.

Profiles cannot silently expand transfer/spend/provider permissions, remove approval requirements or change the Hyperframes/vertical-video contract. Source taste doesn't make unsupported facts publishable.

## Resolution

Merge studio defaults → profile ancestors then selected profile → topic preferences → project overrides. Select profile from explicit project profile_id, otherwise topic profile_id, otherwise source profile_id, otherwise studio default_profile_id. Project topic_id/source_id supply context when not passed explicitly. Resolve a multi-source signal to an intended context rather than merging contradictory profiles arbitrarily.

Nested objects merge recursively. Lists replace; [] clears. Null explicitly clears; missing keys inherit. Preserve unknown fields. Missing IDs, cycles and contradictory explicit project contexts are errors.

```sh
python3 <skill-directory>/scripts/resolve_preferences.py --workspace <path> --topic <id> --source <id> --project <id>
```

Context flags are optional. --profile selects explicitly but must agree with an explicit project profile. The report includes effective preferences, contexts and contributing-file hashes, draft profiles and unresolved video fields. Resolution does not establish tool readiness. It never writes settings, approves anything or advances a stage.

## Conversational changes

Determine scope: defaults, named profile, topic, this project or future projects. Show old → new and impact. A fully specified user command authorizes that exact local change; ambiguous interpretation needs proposal approval. Preserve unknown fields/history, increment revision, and append actual request, scope, timestamp and changed-file hashes to settings/changes.json.

Repeated feedback may suggest a persistent rule; don't activate it without approval. Project corrections apply to that project by default. “Use timelines by default for history explainers” saves the expressly requested persistent rule.

## Freeze projects

Before topic review save the helper report as preferences.json plus a human-readable summary. Set project.json preferences_path to preferences.json. Copy selected brand/frame/script references into context/ with a hash manifest. The topic gate approves profile, overrides and deliverable scope. Research-only, script-only, post-only and full-video scopes are supported.

Approved projects read their snapshot, not live defaults. Read it with `resolve_preferences.py --workspace <path> --project <id> --frozen`; verify its hash against the corresponding approval record separately. The helper reads without enforcing approval. Profile changes affect future projects. “Apply this profile to this episode” creates a new snapshot revision, shows a diff, and invalidates affected gates: research choices → plan/research; narrative → editorial; visuals/motion → storyboard; voice/captions → earliest affected editorial/storyboard/assets stage; and dependent descendants. Preserve unaffected evidence. Never overwrite reviewed preferences.json or context files: save subsequent proposals under preferences/r2.json and context/r2/, incrementing the revision. A preference-change approval records the diff, new snapshot/context hashes, affected gates and original request. Switch preferences_path only after approval. A changed topic angle, scope or deliverables returns to topic review; otherwise earlier gates keep their original snapshot dependencies, and affected gates depend on the new preference-change approval. This avoids invalidating the original topic approval merely by editing a script style. Verify the selected snapshot version and its approval on resume.

Operational setup approvals and profile/monitor change records are separate. Save immutable settings/policy/r1.json containing only data_policy, budget, workflow, tools and capability authorization, and approve that operational snapshot. Keep defaults, profile routing, monitor lists and runtime status out of its hash scope; review those with their own records. Compare current operational fields to the approved policy before acting, and require a new policy revision for changed authorization. Routine creative configuration edits do not invalidate unrelated frozen projects. Tightened data/spend permissions constrain all active work immediately; stop newly disallowed actions before proceeding.

## Version-1 compatibility

The resolver supports old top-level audience/topic/language/duration/video/destination settings without inventing a profile selection. Initializer adds new draft templates without overwriting old files; added profiles stay unused until explicitly adopted. Offer a migration diff, preserve artifacts/approvals/brands, and never claim migration approved merely because initialization ran.
