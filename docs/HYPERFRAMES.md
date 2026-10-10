# Hyperframes review and production choices

Vid Studio uses **Hyperframes only** for HTML composition and video rendering. The host agent orchestrates the workflow. Research, evidence, data, approvals, editable scenes, media, and outputs remain in the local workspace; optional hosted processing is configured explicitly.

## Review baseline

Reviewed official repository commit `affa4d53cf86334c18d0476955fce3f4f73f6a06` and published CLI `hyperframes@0.8.144`, with GSAP `3.14.2`. Source and published package versions agreed at review time. Independent orchestrator tasks reviewed the technical contract and design/evidence/audio quality separately. This pack does not vendor the upstream runtime or copy its complete skill catalog.

The review covered the router, core composition contract, CLI and command references, creative direction, animation adapters and transitions, keyframes, registry, media resolution, audio, faceless-explainer workflow, maps/charts, initialization side effects, validation JSON, preview/render, and optional rendering/import paths. For future upgrades, review the actual installed version's help and source, approve the change, and rerun the starter and an affected episode.

## Video-enabled production path

The ongoing studio can start with research and monitors first; defer this video toolchain until selected. Profiles and project overrides supply editorial/creative choices (see the setup outline).

1. Approve video setup: local toolchain, dependencies/downloads, brand/frame direction, format, source scope, voice route when selected, budget and processing policy.
2. Approve topic, research plan, sourced research/data, script and selected post package, and detailed portrait storyboard in order.
3. Approve selected assets and provenance: narration and aligned captions when enabled, approved reading holds for silent timing, and the chosen charts/imagery.
4. Author Hyperframes scene compositions with local GSAP and frozen dependencies.
5. Run browser/layout/contrast/motion checks; inspect proof frames and the editable Studio preview. Obtain preview approval before encoding.
6. Render a versioned `looks` draft, review its actual decoded picture and selected audio, then obtain approval for `delivery` export.
7. Inspect the final delivery package and obtain final approval. Publishing is separate.

The basic authoring example is `skills/vid-studio/assets/hyperframes-starter/`: a silent nine-second 1080×1920 motion study with three scene sub-compositions. It demonstrates progressive disclosure, connector animation, deliberate typography, and a stable takeaway. It is not a researched episode, a brand template to apply indiscriminately, or a substitute for narration and content review.

## Design standard

The setup produces an approved video-specific `frame.md`, with portrait title/mechanism/chart samples. Episode storyboards include actual keyframes, source-backed chart end states, explanatory motion, selected narration cues and caption placement, and readable holds. Use portrait-native hierarchy and diagrams rather than shrinking a wide slide into a phone frame.

Motion reveals relationships and steers attention. It does not invent temporal data, overshoot quantitative marks, move labels needlessly, or force a background to breathe. Reusable registry primitives are inspected and adapted to the approved brand and evidence. A coherent visual argument, correct data and intelligible selected narration matter more than effects count, fps, or resolution.

## Capability coverage and selection

**Core and modular compositions:** main HTML, timed clips, editor lanes, explicit layering, local scene templates, variables, media placement, and paused registered timelines. Every project has static approved duration and unique IDs. Runtime-owned clip visibility and scene-local media timing are preserved.

**Creative direction:** video-specific design specs, style presets, typography, scene/beat planning, explanatory story spine, source-traceable visuals, and phone-size review. Upstream aesthetic defaults are suggestions; user-approved branding and data truth win when they conflict.

**Animation/keyframes:** default GSAP plus supported CSS, WAAPI, Anime.js, Lottie, Three.js, shaders and other seek adapters when justified. Camera moves require explicit poses and preserve subject identity. Technical keyframe diagnostics are paired with actual painted frames. 3D/WebGL is optional, with GPU availability verified before committing to it.

**Registry:** intent-based block/component search, reviewed downloads, local source freezing, dependencies, and correct composition/snippet wiring. Landscape blocks require portrait reflow. Replace sample figures and inspect chart scales, bundled sounds, fonts, external dependencies and licenses.

**Charts/maps:** local approved datasets, calculation provenance, fixed truthful domains, labels/units/uncertainty, and baked geography. Registry charts are visual primitives; they do not validate evidence. Live API fetches and CDN geography are removed from render dependencies.

**Media/voice/captions:** local user assets, licensed real material, authored diagrams, optional generated media, recorded/local or explicitly permitted hosted narration, transcription with correct language, and corrected word/phrase timings. Missing providers do not authorize a hosted fallback. Generated illustrations are not presented as documentary evidence.

**Audio:** separate voice/music/effect/source tracks, audio groups, gain/automation, supported effects, and optional voiceover carve/ducking. Loudness/true peak are measured on the decoded export; listening checks remain distinct from numeric analysis. Music is optional.

**Validation/review:** lint while authoring; check for browser/runtime/layout/motion/contrast; sidecars for real motion intent; boundary/midpoint/final-frame snapshots; Studio review; encoded playback, full decode, ffprobe and audio measurements. Empty or skipped audits cannot pass. Meaningful static holds are allowed.

**Website capture:** optional for actual site/UI walkthroughs. Failed/blocked captures are not usable output. A URL used as a research source does not imply the video should become a website tour or inherit that website's design.

**Design import:** optional Figma/Open Design/other supplied design handoff. Use existing exports/tokens where available; external account access/import is approved separately. Translate design states into motion rather than rendering static slides without explanation.

**Audio-reactive/music-led work:** precompute waveform/band or beat data locally if this serves the brief. Explainer narration normally drives pacing. Do not introduce live WebAudio or microphone dependencies into deterministic export.

**Batch/variables:** useful for approved repeated layouts or versions. Freeze per-output data and duration; retain per-episode/version approvals. A batch command cannot implicitly approve every output.

**Transparent overlays/HDR/shader transitions:** optional specialized outputs; verify format/GPU/alpha and background layering contracts. Standard explainer delivery remains the approved portrait MP4 unless the destination requires something else.

**Rendering:** local is the default. Docker can improve environment reproducibility, but record the actual image digest/browser/encoder rather than promising byte identity across arbitrary hosts. Hosted cloud, AWS Lambda and Google Cloud Run are optional Hyperframes execution paths; they require upload scope, credentials, costs and output retrieval approval. No account deployments are created by installing this pack.

**Studio edits/history:** read the current editable project before changing it. Query stable selected-element context if available. User changes are preserved and invalidate affected reviewed hashes. Tool history supports recovery but does not replace the workspace's approval record.

## Deliberate adaptations of upstream behavior

- Upstream creation workflows may combine approvals or run autonomously; vid-studio keeps its granular gates and adds composition-preview approval before encoding.
- Some general creative references suggest ambient movement; explainers prioritize stillness when reading or understanding resolved evidence.
- Chart minimalism cannot remove labels/scales required for honest interpretation.
- `init` can refresh skills and transcribe supplied media. Controlled setup opts out of implicit updates/transcription and approves these capabilities separately.
- Pinned npm CLI does not pin independently updated upstream skills or mutable registry content. Record each separately.
- Telemetry/automatic feedback and public publishing are disabled in the local-first path. Scoped downloads and model processing are still disclosed accurately.
- Doctor reports optional absent tools too; assess actual required checks. Browser launch must be proven by the project check.
- Documentation may lag source (timing triggers and variable bindings are examples). Follow the approved version's source/help and observed checks, recording discrepancies.

## Validation evidence

See [VALIDATION.md](VALIDATION.md) for the performed tests and limits. The included starter and export helper are technically exercised; an actual audience/topic/voice episode still needs all creative, factual, and audio reviews. The pack guides agent behavior; its approval records are not an enforcement service.

## Official sources

- [Repository and capability map](https://github.com/heygen-com/hyperframes/tree/affa4d53cf86334c18d0476955fce3f4f73f6a06)
- [Core](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-core/SKILL.md)
- [CLI](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-cli/SKILL.md)
- [Creative](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-creative/SKILL.md)
- [Animation](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-animation/SKILL.md)
- [Keyframes](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-keyframes/SKILL.md)
- [Registry](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-registry/SKILL.md)
- [Media](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/media-use/SKILL.md)
- [Audio](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-audio/SKILL.md)
- [Explainer workflow](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/faceless-explainer/SKILL.md)
