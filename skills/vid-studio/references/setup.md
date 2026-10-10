# Workspace setup

Follow [onboarding.md](onboarding.md) and [profiles.md](profiles.md). Gather tastes conversationally in short rounds, then present a filled setup proposal. The studio can launch for monitoring/research while video capabilities are deferred; do not force immediate production.

## Proposal contents

- Absolute workspace location; keep production data separate from the public skill repository.
- Studio defaults and named profiles: research interests/source tastes/depth/freshness/angles/ranking, audience, script/post structure and templates, languages, tone, duration, outputs and destinations.
- Vertical format, visual style, reference videos if supplied, fonts, colors, logo, caption style, narration preferences. Missing brand assets can be designed as a draft for setup review.
- Data policy: local storage with hosted processing allowed, local processing only, or per-service rules. Identify permitted model, voice, media, and rendering services and what each receives. Local storage does not imply local processing.
- Existing capabilities: browsing/search, terminal, Python, Node.js 22+, FFmpeg/ffprobe, Hyperframes/Chromium, narration and media tools, scheduler. Read-only capability checks are allowed while preparing the proposal. Report unknown availability accurately.
- Spend limits and whether external jobs require approval each time. Default to no paid calls until scoped authorization exists.
- Sources/topics and one-off or recurring research. Monitoring cadence and publishing cadence are separate. Timezone and approved collection scope for recurring runs.
- If video setup is selected now: Hyperframes-only toolchain and exact version, pinned local dependencies, telemetry disabled by default, scoped registry/model downloads, and brand/frame.md with portrait title/mechanism/chart samples. Read [hyperframes.md](hyperframes.md), [design-motion.md](design-motion.md), and [data-media.md](data-media.md).
- All stage gates enabled, publishing disabled, cross-model review disabled.

## After setup approval

1. Run the bundled initializer using its resolved absolute skill path:
   `python3 <skill-directory>/scripts/init_workspace.py --workspace <absolute-workspace-path>`
   It creates missing files only; it does not install dependencies, start schedules, or approve anything.
2. Fill studio.json (operational policy and defaults), profiles/default.json and any requested additional profiles, ONBOARDING.md, and the selected brand/frame references with approved settings. Mark profile status approved only when its reviewed content was approved; preserve unresolved values. Save settings/policy/r1.json with the approved operational fields only, as defined in profiles.md. The completed setup approval hashes that immutable policy, toolchain evidence and reviewed setup results; profiles and monitor configuration use separate change records. Save the reviewed proposal locally, and record its approval in `setup-approval.json` following workspace.md. If material settings differ from the approved proposal, ask for review again.
3. Configure only capabilities selected for immediate setup. If video setup is deferred, record it as not configured and do not install Hyperframes or voice/media dependencies yet. Otherwise prepare the pinned Hyperframes toolchain according to hyperframes.md with a local lockfile/capability report. Execute only approved actions. Preserve existing agent configuration. Do not replace AGENTS.md or CLAUDE.md. If helpful, propose a short project-scoped pointer to this skill and the workspace.
4. If scheduling was approved and the host supports it, create the schedule and save its identifier and instructions locally. Otherwise offer the host's manual scheduling instructions or a separately reviewed OS schedule; never claim a schedule exists without confirmation.
5. Update STATUS.md and present setup results with missing prerequisites. Activate approved monitors after completed setup approval; present the inbox/status and let the user choose the next activity. Begin a content project only when requested and after applicable setup capabilities are ready. The proposal authorizes setup execution; approval of the completed setup authorizes the next stage.

## Scheduled instruction

Adapt to the host, keeping these requirements: “Use vid-studio with workspace <path>. Read studio.json, local status, approved profile routing and monitor configuration. Check only enabled nonarchived sources within the approved monitoring scope. Save new signals with source URLs and timestamps; deduplicate against previous runs. Work only within an authorized stage. Stop and report any pending approval; never approve, publish, send, or incur unapproved costs. Update STATUS.md.”

Store approved schedule timezone, cadence, host identifier, and scope in configuration-only `monitoring/schedule.json`. Store run timestamps, outcomes, and last completed collection time in `monitoring/state.json` under its schedule key. Routine runs must not change approved schedule/configuration hashes. A scheduled collection may refresh the inbox while projects wait for review, but may not alter reviewed project artifacts.
