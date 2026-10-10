# Hyperframes production contract

Hyperframes is the only composition and video-rendering framework in vid-studio. FFmpeg/ffprobe may prepare or inspect assets and exports. A missing browser or failed Hyperframes render is a blocker; preserve the project rather than silently switching frameworks.

This guide was reviewed against published CLI **0.8.144** and official source commit **affa4d53cf86334c18d0476955fce3f4f73f6a06**. Versions are a validated baseline, not a promise about future releases. Check the chosen version's help/source when behavior differs. Do not mix an older CLI with instructions from an unreviewed newer skill.

## Approved setup and dependencies

Require Node.js 22+, FFmpeg/ffprobe, and a Chromium browser that Hyperframes can launch. Inspect `doctor --json` and its actual checks; an exit code of zero does not mean readiness. Optional Docker/transcription/TTS/music failures do not block local silent/recorded-narration rendering when those capabilities are not selected. Verify browser launch through `check` before declaring readiness.

Install into the selected workspace, after setup approval, with exact versions and a lockfile. Example from its `tools/` directory:

```sh
npm install --save-exact hyperframes@0.8.144 gsap@3.14.2
```

Resolve the installed binary absolutely (`<workspace>/tools/node_modules/.bin/hyperframes`). In the commands below `HF` means that resolved binary, not a shell variable the user must configure. A project-local wrapper can invoke it consistently. Record versions and lockfile hashes in `tools/toolchain.json`, including the browser and FFmpeg actually used. Do not auto-upgrade an active production project.

Our references and starter are sufficient for the basic path. For advanced features, read the matching official domain skill/source at the reviewed commit. Optional upstream skill installation belongs in approved setup. Standalone upstream skill updates track `main` separately from the pinned npm CLI; record their commit/hashes too. Do not install all upstream workflows just to make one explainer.

For local-first operation, set `HYPERFRAMES_NO_TELEMETRY=1` on CLI invocations and `HYPERFRAMES_SKIP_SKILLS=1` when initializing. At the reviewed version `--skip-skills` is ignored; the environment variable prevents init's automatic skill update. Do not run feedback/events/publish or upload research as an implicit part of rendering. Cloud render, external media providers, model downloads, and registry downloads remain governed by setup authorization. Never fall through from a selected local provider to a hosted one without consent.

## Scaffold at the composition stage

Use a new `07-video/hyperframes/` directory; do not initialize over existing work:

```sh
HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_TELEMETRY=1 HF init <project>/07-video/hyperframes --non-interactive --resolution portrait --skip-transcribe
```

`HF` is explanatory notation: replace it with the resolved executable path and quote paths containing spaces. Supplying audio/video to init can trigger transcription; keep media staging deliberate. Apply the approved dimensions, static root duration, fps, brand and scene timings. The bundled [portrait starter](../assets/hyperframes-starter/index.html) is a tested, silent three-scene authoring example, not an approved episode or a complete visual style for every topic. Copy local GSAP from `tools/node_modules/gsap/dist/gsap.min.js` to the composition's `assets/gsap.min.js`; do not rely on a CDN at render time.

**Init also copies AGENTS.md and CLAUDE.md regardless of the skip-skills setting.** Immediately inspect these newly generated files before another agent enters the composition directory. In this new scaffold, replace only those generated files with the bundled [agent policy](../assets/hyperframes-starter/agent-policy.md), adding the resolved installed skill path, workspace path, and project path. Save the original generated versions in a toolchain audit directory outside the active instruction tree. This is part of approved vid-studio setup, not permission to replace pre-existing user guidance. Never init over an existing project; preserve and reconcile user-owned instructions explicitly.

## Composition invariants

- Top-level index.html: visible root in the body, no template wrapper. Declare `data-composition-id`, `data-width`, `data-height`, and finite static `data-duration`. Size root CSS to 100%; the runtime applies canvas pixels.
- Each timed scene: stable unique IDs, `data-start`, `data-duration`, and `.clip` by convention. Track index is an editor lane; CSS z-index determines stacking. End states must resolve before a clip's half-open end boundary.
- GSAP: one paused timeline per composition, registered at `window.__timelines[compositionId]` after all tweens are constructed. Registration can follow `document.fonts.ready`. Never call play for render-critical animation.
- Animate inner visual wrappers. Framework-owned clip visibility must not be driven by display/visibility/autoAlpha tweens. Avoid CSS transform centering on the same element whose transforms GSAP animates; use layout containers or explicit fromTo states.
- State must derive from composition time. No clocks, event/scroll/hover triggers, uncontrolled timers, unseeded randomness, or live API data. Precompute visual/audio analyses and freeze every dependency locally.
- Sub-compositions: styles, markup, and scripts belong inside the template transport; match host composition ID, inner ID, and timeline registration key. Give descendants globally unique prefixed IDs. Do not manually nest child timelines that Hyperframes already drives.
- Give every audio/video a unique ID. Let the framework own seeking and playback. Avoid timing both a video and a plain timed ancestor. Scene-local media timing within sub-compositions is supported. Use baseline data-volume and documented data-automation envelopes for sound.
- Ship licensed fonts with explicit local @font-face weights/styles and required glyphs. A system alias is acceptable for a technical fixture; it is not a reproducible brand font. Local font lookup alone is machine-dependent.
- Root duration is read before scripts run. If approved narration changes the length, update the authored root duration and dependent scene timings; a variable cannot rewrite an explicit root duration after load.

## Registry and advanced capabilities

Before rebuilding a named chart, caption treatment, map, mask, or transition, search the catalog by visual intent in English:

```sh
HF catalog --query "reveal a process diagram step by step" --json
HF add <chosen-name> --no-clipboard --json
```

Search/install only within approved download scope. Inspect installed source, sample content, dimensions, dependencies, sounds, and licensing. Reflow landscape blocks for portrait, replace demo figures with approved local data, freeze map geometry, and verify mounted scenes. Blocks are sub-compositions; components merge into the host's markup/style/timeline. Persist downloaded source and hashes, rather than depending on a mutable registry URL during render.

GSAP is the default motion runtime for simplicity. CSS/WAAPI/Anime.js/Lottie/Three.js and shader transitions can be used through the supported seek adapters when their benefit is clear; read the relevant official adapter and prove arbitrary-time seeking first. 3D/WebGL increases GPU requirements. Do not add it merely to claim quality. With shaders or HDR layered compositing, use a full-bleed child for the background instead of depending on a composition-root fill.

Other optional Hyperframes capabilities: website capture for actual site walkthroughs; caption styling; precomputed audio-reactive animation; variable-driven batch rendering; Figma/design imports; transparent overlays; Docker and approved cloud/Lambda/Cloud Run rendering. They are not required for an evidence-based explainer. A blocked capture is unusable; a batch must not bypass per-episode approvals; hosted paths require transfer/cost approval. Consult the capability review in the repository docs when choosing scope.

## Validate, preview, approve, encode

```sh
HF lint <composition-dir> --json
HF check <composition-dir> --json --snapshots --at-transitions
HF keyframes <composition-dir> --json --runtime all
HF snapshot <composition-dir> --at 0.5,3.5,6.5
HF preview <composition-dir> --background
```

Use lint while authoring; check includes lint, so omit redundant lint immediately before the final check. Snapshot timestamps above are examples: inspect each scene's entrance, middle, settled state, boundaries, and last frame at the project's actual proof times. Require `ok: true`, `browserSkipped: false`, and meaningful nonzero sampling. Empty browser audits are not passes. Record warnings and fixes/justified intent; use narrow documented allowances rather than muting audits on scene roots.

Add `*.motion.json` sidecars where they express storyboard intent (ordering, appearsBy, staysInFrame). `keepsMoving` is optional: a readable hold is valid; do not introduce decorative jitter to satisfy a liveness test. Focused keyframes `--shot` checks plus actual images prove important pose transitions. See [quality.md](quality.md).

Verify the persistent Studio URL is reachable, use its printed project route, and keep it alive during review. Studio edits alter source files; recheck hashes before rendering. **Composition/preview approval authorizes the draft encode; no encode before it.** Then:

```sh
HF render <composition-dir> --fps 30 --quality looks --output <project>/07-video/draft-v1.mp4
```

Use approved fps, not necessarily the example's 30. After rendered-draft approval, export with `--quality delivery` to a new final path. `draft` quality is only for explicitly authorized low-cost iteration; never call it delivery quality. Inspect encoded streams, decode/playback, sound, and final frames. Save render logs and source/environment hashes. Same source/time should produce the same scene state; byte-identical output across arbitrary machines is not guaranteed. Pin container digest and actual browser/encoder environment when strict reproducibility matters.

## Official references

- [Core contract](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-core/SKILL.md)
- [CLI commands and references](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-cli/SKILL.md)
- [Registry](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-registry/SKILL.md)
- [Current documentation](https://hyperframes.heygen.com/introduction)
