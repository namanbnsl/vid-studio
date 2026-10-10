# Set up and operate your studio

## 1. Install and begin onboarding

Push this repository to GitHub yourself and use the [README installation command](../README.md#install-after-pushing-to-github). Keep `skills/vid-studio/` and its references, scripts, and assets together. Refresh skill discovery in your agent if needed. Installation makes instructions available; it does not grant account access, install production dependencies, or create schedules.

Choose a separate local data workspace and invoke `vid-studio`:

> Set up /absolute/path/to/my-studio for ongoing energy research. I want weekly sourced briefs for policy readers. Ask about my research and writing tastes first; defer video tools and brand design.

The agent asks a few useful questions at a time: goals, audiences, domains, languages, outputs, research preferences, editorial taste, creative references, and operations. Liked or disliked examples help describe taste. You do not need to answer every field or edit JSON manually. See [conversational onboarding](../skills/vid-studio/references/onboarding.md).

Review a proposal covering studio defaults, named profiles, initial sources/topics, immediate setup actions, unresolved choices, and deferred capabilities. Specify local storage versus local processing, allowed services and inputs, credentials handling, costs, and collection scope. Local files can coexist with approved hosted processing; strict local processing requires suitable local tools.

After approval, the bundled Python initializer creates missing templates without overwriting existing files. The agent fills the approved configuration and records setup decisions. The initializer does not install dependencies, start schedules, or approve setup. Review completed setup and its capability report before monitors are activated or content projects begin. Keep credentials out of the workspace and public repository.

## 2. Shape defaults and profiles

Use studio defaults for shared preferences and named profiles for different brands, audiences, or series. Customize research interests/exclusions, source priorities, freshness, depth, evidence expectations and ranking; editorial tone, language, complexity, exact sections, templates, pacing and endings; and brand, layout, motion, voice, music and captions. WhatsApp formatting and review presentation are editable too. Large templates and examples can stay in local files.

> Create an analytical profile. Use templates/analysis.md with exactly these sections: finding, evidence, counterargument, uncertainty, takeaway. No hook, emojis, or CTA.

> Clone it for students and simplify jargon. Keep the analytical profile's research standards. Show the differences.

> Always use timelines for history explainers in the history profile. Shorten this episode's introduction only.

The first persistent instruction changes the named profile; the episode correction stays local to that project. The agent shows the change and impact, preserves custom settings, and records authorization/history. A precise command authorizes that exact local change; unclear scope needs clarification. Suggested rules from repeated feedback require approval before becoming persistent.

Effective preferences merge in this order: **studio defaults → profile ancestors → selected profile → topic preferences → project overrides**. Nested objects merge; lists replace; an empty list or `null` clears a value. Profile selection comes from the project, otherwise topic, otherwise source, otherwise studio default; an explicit selection must agree with an explicit project profile. Multiple sources need a deliberate context rather than an arbitrary blend of profiles.

Before topic review, each project saves a preference snapshot and human-readable summary, plus copies/hashes of selected script, brand, and frame references. Approved projects use that frozen snapshot. Changing a default or profile affects future projects. An explicit active-project request such as “Apply the revised science profile to this episode” creates a snapshot revision, shows the diff, and invalidates affected approvals and downstream stages while preserving unaffected evidence. Tightened data/spend permissions constrain active work immediately.

The read-only helper can inspect resolution:

```sh
python3 <skill-directory>/scripts/resolve_preferences.py --workspace <absolute-workspace-path> --profile science
```

Optional `--topic`, `--source`, and `--project` flags supply live draft context. To resume reviewed work, use `--project <id> --frozen` to read the selected saved snapshot, then verify its approval hashes. The report includes preferences, contributing layers, and file hashes. It does not copy reference contents, write settings, enforce approvals, or advance stages. See [profiles and snapshots](../skills/vid-studio/references/profiles.md) for details.

## 3. Manage monitors, recurring research, and the inbox

Review source/topic suggestions before enabling them. Sources can be websites, feeds, search queries, or imported alerts; topics can be one-off or recurring. Configure watch conditions, filters, profile routing, cadence, timezone, and novelty criteria conversationally.

> Suggest primary sources for battery policy, with actual links and reasons, for my analytical profile.

> Add this feed to that profile. Check every Friday at 10:00 Asia/Kolkata for regulatory changes; exclude product launches.

> Edit the query to include recycling rules. Pause the battery topic for a month. Archive the obsolete source while retaining its evidence.

> Show enabled monitors and their real schedule status. Show the inbox with relevance, novelty, source dates, duplicates, and pending decisions.

Pause/resume retains findings and checkpoints. Removal defaults to disable/archive and preserves research and projects. Collection checks enabled, nonarchived records in approved scope, saves local evidence, deduplicates against previous runs, and can return “no new relevant findings.” Failed retrievals do not count as successful collection.

Monitoring cadence is separate from publishing cadence. If the host has a scheduler and you approve its scope, the agent creates/reconciles the task and records its actual identifier and confirmation. A saved cadence alone is not a schedule. Without a scheduler, run collection manually or review an alternative scheduling proposal. Changing cadence or pausing a monitor must reconcile any real host task within approved scope.

Collection can refresh the inbox while a project waits for approval. It cannot rewrite reviewed artifacts, automatically select episodes, silently learn preferences, send notifications without authorization, or publish. See [studio management](../skills/vid-studio/references/manage-studio.md).

## 4. Choose outputs from a finding

> Research this inbox candidate as a brief only, using the analytical profile.

> Create a post and script from the approved brief. Use my exact template; omit WhatsApp and video.

Choose deliverable scope at topic review. Research-only ends at research approval; script/post-only ends at the applicable editorial gate. The schema-2 draft defaults include video and WhatsApp, but both are configurable. Inbox or management requests do not start production. Recurring research can continue without generating any content; separately selected episodes receive their own project IDs and approvals.

Settings, monitor configuration, inbox findings, evidence, project snapshots, editable sources, and approval records live in your local workspace. Resume the same workspace in a fresh session or compatible agent; it reads status and verifies reviewed versions before continuing.

## 5. Add video capabilities when needed

> I now want portrait videos for the science profile. Propose the missing tools, voice route, brand/frame samples, costs, and downloads for approval.

Research setup can finish while video capabilities remain deferred. Missing tools block only the activities that need them. The capability report must distinguish available, missing, and untested integrations; the skill does not supply a universal search, narration, or scheduler service.

For video, Hyperframes is the sole framework and the format stays vertical 9:16. Suggested defaults are 1080×1920 at 30 fps; duration, visual style, voice, motion, captions, and assets remain configurable. Approved setup uses pinned local Hyperframes/GSAP dependencies and a lockfile, Node.js 22+, compatible Chromium, and FFmpeg/ffprobe for the supported local render/inspection path. The reviewed baseline is Hyperframes `0.8.144` and GSAP `3.14.2`; upgrades require review and affected validation. Telemetry is disabled by default. Voice recording/generation and image/media tools are configured only as needed and permitted.

Follow the [Hyperframes setup and authoring contract](../skills/vid-studio/references/hyperframes.md), [design/motion guidance](../skills/vid-studio/references/design-motion.md), and [capability review with official source links](HYPERFRAMES.md). Preserve existing agent configuration. The agent installs only approved dependencies/downloads; the runtime is not vendored here.

## 6. Review each applicable production stage

A full portrait video prepares these deliverables in order:

1. **Topic:** angle, audience, source leads, selected profile/snapshot, and output scope.
2. **Plan:** questions, boundaries, source strategy, and data needs.
3. **Research:** sourced brief, claim ledger, saved evidence, caveats, and takeaway.
4. **Editorial:** configured script/post structure, scene IDs and factual references where applicable; WhatsApp copy only if selected.
5. **Storyboard:** layouts, meaningful motion, charts, narration/caption plan, asset sourcing, and cost/transfer scope.
6. **Assets:** selected narration, imagery, chart data, caption timings, and provenance. Intentionally silent or captions-off outputs omit those components.
7. **Composition preview:** editable portrait Hyperframes scenes, local dependencies, checked proof frames/QA, and reachable Studio preview. Approval is required before encoding.
8. **Video draft:** playable render, editable sources, and technical/visual/audio QA.
9. **Export:** final approved output package, selected captions/cover/copy, and delivery manifest.

Every applicable stage pauses for explicit approval of its reviewed version. Partial approvals and revisions leave that stage open; “finish the video” does not approve future outputs. Changes to approved artifacts invalidate affected downstream approvals. Resume verifies hashes/dependencies and returns to the earliest affected gate. Export approval completes local delivery; sending WhatsApp copy or publishing remains a separate authorized action.

Approval records are an agent-followed workflow, not a separate enforcement engine. The pack provides instructions, templates, a portrait motion starter, and helpers; actual research and production use your configured tools. Cross-model review and automatic publishing are disabled initially.

## Existing workspaces and acceptance checks

For an older workspace, request a migration proposal and review its diff before adoption. The resolver supports legacy top-level settings; newly added draft profiles remain unused until explicitly adopted. Preserve existing artifacts, approvals, brands, and user edits. Initialization alone is not migration approval.

Start with a small research-only trial: verify proposal/completed-setup review, source evidence, exact profile/template behavior, output scope, local snapshots, resume, and reapproval after an affected change. Check that missing tools and absent schedules are reported accurately. Before enabling recurrence, verify the approved scope and real scheduling status.

When adding video, run a short episode trial with your actual brand and narration. Verify every production gate, checked Studio preview before encoding, playable portrait output, and an accurate account of QA performed. The [rendered motion study](../examples/portrait-motion-study.mp4) is a silent technical fixture, not a researched episode or creative-quality guarantee. See [validation evidence and remaining limits](VALIDATION.md) before relying on optional integrations.
