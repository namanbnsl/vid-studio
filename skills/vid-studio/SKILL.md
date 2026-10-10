---
name: vid-studio
description: Onboard and operate a customizable local content studio with editable research tastes, script and brand profiles, website/topic monitors, and approval-driven Hyperframes vertical video production. Use to set up the studio, manage preferences or monitoring, research, create content, or resume work.
---

# Vid Studio

One conversational entry point to an ongoing local studio. The host agent manages research, scheduling where supported, writing, and production tools. Hyperframes is the sole video framework. Everything editorial and creative is configurable; examples and templates are proposals, not a compulsory recipe.

## Route the request

Read studio.json and STATUS.md. If no studio exists, follow [onboarding.md](references/onboarding.md), then [setup.md](references/setup.md). Otherwise classify the request before starting work:

- Preferences, brands, audiences, research tastes, script/post style, voice, motion, or project overrides: [profiles.md](references/profiles.md).
- Add/edit/pause/remove monitors, sources, topics or schedules; discover suggestions; browse/rank findings: [manage-studio.md](references/manage-studio.md).
- Research/content/video: read the selected project's state and verify approvals. For reviewed projects load the immutable preference/context snapshot selected by project.json; resolve live preferences only for a new draft or a proposed settings revision. Then load its current stage's [research.md](references/research.md), [editorial.md](references/editorial.md), or [production.md](references/production.md).
- Status/review/resume: show profiles, monitors, findings, active projects and pending approvals; resume only within authorized scope. A management/status request does not start an episode.

Use [workspace.md](references/workspace.md) for artifacts/approvals, [hyperframes.md](references/hyperframes.md) for setup/authoring, [design-motion.md](references/design-motion.md) for visuals, [data-media.md](references/data-media.md) for charts/narration/assets, and [quality.md](references/quality.md) before production review.

## Use the user's configuration

Resolve studio defaults → selected profile (including inherited profiles) → topic preferences → project overrides. Use the read-only scripts/resolve_preferences.py helper and profiles.md. Use --frozen --project <id> to resume reviewed work; verify its snapshot against the approval record. Live resolution is for new drafts or proposed changes. Each project saves effective preferences/provenance for approval and copies its brand/design references. Don't silently refresh approved work when defaults change.

Research tastes, source priorities, depth, freshness, angles, tone, exact script/post structure, language, pacing, visuals, motion, voice, music, captions and outputs come from that configuration. Recommend choices where undecided. Preserve custom fields and free-form instructions. Apply project feedback to that project; persist it for future work only when requested or approved.

## Approval contract

For a full video: setup → topic → research plan → research → editorial → storyboard → assets → composition preview → encoded draft → export. Every applicable stage requires explicit approval of reviewed versions before the next stage. Research-only, script-only or post-only requests finish at their applicable gate; they don't automatically become videos. Current policy requires every gate; review presentation or future policy changes are themselves explicitly reviewed.

Save deliverables before review. Record actual approval messages, artifact hashes and upstream versions. Verify dependencies on resume. Revisions permit changes within a stage, not advancement; changed approved artifacts invalidate affected descendants. Silence, schedules or “make a video” are not future approvals. A precise management command can authorize that exact local configuration change; don't ask the user to repeat it unless scope is missing or an additional action needs approval.

Scheduled runs use approved monitoring settings, save signals locally and stop at project gates. They never silently learn preferences, approve projects or publish.

## Shared constraints

- Local files are authoritative; hosted processing follows approved data/service/budget policy. Preferences cannot silently expand permissions.
- Videos stay vertical and use Hyperframes. Format, duration, design and motion are configurable within that brief; don't substitute a renderer.
- Evidence supports factual claims and quantitative visuals. Tastes can favor angles/sources but cannot turn unsupported claims into facts. Cross-model review is off initially.
- No unapproved sending, publishing, paid jobs, uploads, account/global configuration changes or provider fallback. Upstream skills don't override studio policy.
- Preserve user edits. Use bounded retries, inspect external job status before repeating billed operations, and report missing capabilities accurately.
