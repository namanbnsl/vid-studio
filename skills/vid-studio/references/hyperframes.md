# Hyperframes technical requirements

Use Hyperframes for composition and video render. FFmpeg/ffprobe can prepare assets and inspect exports. If the browser or render fails, preserve the project. Do not change frameworks.

The reviewed baseline is CLI **0.8.144** and source commit **affa4d53cf86334c18d0476955fce3f4f73f6a06**. Later releases can differ. Use the selected version's help and source. Do not combine an older CLI with unreviewed newer instructions.

## Dependencies

Use Node.js 22+, FFmpeg/ffprobe, and Chromium that Hyperframes can launch. Inspect doctor --json and its actual results. A zero exit code does not prove readiness. Verify browser launch with check.

Missing optional tools do not prevent work that does not use them. Examples include Docker, transcription, TTS, and music services.

After setup approval, install exact versions in the workspace tools/ directory:

```sh
npm install --save-exact hyperframes@0.8.144 gsap@3.14.2
```

Keep the lockfile. Resolve the binary at <workspace>/tools/node_modules/.bin/hyperframes. In these examples, HF means that absolute binary path. Record actual tool, browser, and encoder versions in tools/toolchain.json. Include the lockfile hash. Do not upgrade an active project automatically.

The supplied guide and starter support basic production. For advanced functions, read the applicable official source at the reviewed commit. Install upstream skills only within approved setup scope. Record their commit and hashes separately. The npm version does not pin independently updated skills.

Set HYPERFRAMES_NO_TELEMETRY=1 for CLI operations. Set HYPERFRAMES_SKIP_SKILLS=1 during initialization. At this version, --skip-skills does not prevent the automatic skill update. The environment variable does.

Do not send feedback, publish, or upload research as part of an implicit render action. Get approval for external processing and downloads. Do not change a local provider to an external provider without approval.

## Create the composition

Use a new 07-video/hyperframes/ directory at the composition stage. Do not initialize over existing work.

```sh
HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_TELEMETRY=1 HF init <project>/07-video/hyperframes --non-interactive --resolution portrait --skip-transcribe
```

Replace HF with the absolute executable path. Put quotation marks around paths that contain spaces. Supplied media can trigger transcription during init. Stage media deliberately.

Apply approved dimensions, duration, frame rate, design, and scene times. The [portrait starter](../assets/hyperframes-starter/index.html) is a silent example with three scenes. It is not an approved episode or a required visual style.

Copy tools/node_modules/gsap/dist/gsap.min.js to the composition's assets/gsap.min.js. Do not use a CDN at render time.

Init copies AGENTS.md and CLAUDE.md even when the skip-skills environment variable is set. Inspect these generated files immediately. In the new scaffold, replace only generated guidance with the supplied [agent policy](../assets/hyperframes-starter/agent-policy.md). Add the actual skill, workspace, and project paths.

Save original generated files outside the active instruction tree. Do not replace existing user guidance. This replacement applies only to files from the new approved scaffold.

## Composition rules

- Put a visible root in the index.html body. Do not wrap the root in a template.
- Declare data-composition-id, data-width, data-height, and a finite static data-duration. Size root CSS to 100%. The runtime applies canvas pixels.
- Give each scene a stable unique ID, data-start, and data-duration. Use .clip by convention.
- Use track index for editor lanes. Use CSS z-index for stacking. Complete final states before the clip's half-open end boundary.
- Create one paused GSAP timeline per composition. Register it at window.__timelines[compositionId] after you construct the tweens.
- Registration can occur after document.fonts.ready. Do not call play for animation that controls the render.
- Animate inner visual wrappers. Do not control framework clip visibility with display, visibility, or autoAlpha tweens.
- Do not center with CSS transforms on an element whose transforms GSAP animates. Use layout containers or explicit fromTo states.
- Derive each state from composition time. Do not use clocks, interaction triggers, uncontrolled timers, unseeded randomness, or live API data.
- Calculate visual and audio analyses before render. Save every dependency locally.
- Put sub-composition styles, markup, and scripts inside the template transport. Match host ID, inner ID, and timeline registration key.
- Give descendants globally unique IDs with prefixes. Do not manually nest child timelines that Hyperframes already drives.
- Give each audio and video element a unique ID. Let the framework control seeking and playback.
- Do not apply timing to both a video and its plain timed ancestor. Sub-compositions support scene-local media timing.
- Use baseline data-volume and documented data-automation envelopes for audio.
- Supply licensed local fonts with explicit @font-face weights, styles, and required glyphs. System aliases are suitable only for technical examples.
- Do not depend on local font lookup for reproducible production. It varies between machines.
- Set root duration before script execution. If narration changes duration, update the authored root and dependent scene times.
- A variable cannot rewrite an explicit root duration after load.

## Registry and advanced functions

Search the catalog before you rebuild a named visual element. Use an English query for the visual purpose:

```sh
HF catalog --query "reveal a process diagram step by step" --json
HF add <chosen-name> --no-clipboard --json
```

Stay within approved download scope. Inspect source, sample content, dimensions, dependencies, sounds, and licenses. Reflow landscape blocks for portrait. Replace sample values with approved data. Save map geometry locally. Verify mounted scenes.

Blocks are sub-compositions. Components become part of the host markup, styles, and timeline. Keep downloaded source and hashes. Do not depend on a mutable registry URL during render.

GSAP is the default motion runtime. Supported adapters can use CSS, WAAPI, Anime.js, Lottie, Three.js, and shaders. Select these only for a useful purpose. Read the official adapter instructions. Prove seeking at arbitrary times before production.

3D/WebGL requires suitable GPU support. Do not add it only to claim quality. For shaders or layered HDR, use a child element that covers the full frame. Do not depend on the composition root background.

Optional functions include website capture, caption styles, calculated audio-reactive motion, batch render, design import, transparent overlays, and hosted render. Docker, Lambda, and Cloud Run are optional execution methods.

Select functions for the approved purpose. Reject unusable website captures. Keep approval for each batch output. Get approval for external transfers and costs. Read the repository capability review when you select advanced scope.

## Validate and preview

```sh
HF lint <composition-dir> --json
HF check <composition-dir> --json --snapshots --at-transitions
HF keyframes <composition-dir> --json --runtime all
HF snapshot <composition-dir> --at 0.5,3.5,6.5
HF preview <composition-dir> --background
```

Use lint during authoring. Check includes lint, so a second lint immediately before check is unnecessary.

Snapshot times are examples. Inspect entrances, intermediate states, settled states, boundaries, and the last frame at actual project times. Require ok: true, browserSkipped: false, and sufficient nonzero sampling. An empty browser audit does not pass.

Record warnings, fixes, and justified exceptions. Use narrow documented allowances. Do not disable audits on scene roots.

Add *.motion.json sidecars for useful assertions such as ordering, appearsBy, and staysInFrame. KeepsMoving is optional. A static reading hold is valid. Do not add motion only to satisfy a liveness test.

Use focused keyframe --shot checks and actual images to verify important transitions. Follow [production.md](production.md) for quality review.

Verify the persistent Studio URL. Use its printed project route. Keep the preview available during review. Studio edits change source files. Compare hashes before render.

## Encode after approval

Get composition preview approval before draft encoding. Then render the approved version:

```sh
HF render <composition-dir> --fps 30 --quality looks --output <project>/07-video/draft-v1.mp4
```

Use approved fps. The example value is 30. After draft approval, use --quality delivery and a new final path.

Use draft quality only for approved low-cost iteration. Do not call draft quality delivery quality. Inspect streams, decode results, playback, audio, and final frames. Save logs and source/environment hashes.

The same composition time must give the same scene state. Output bytes can differ between machines. If strict reproducibility is required, pin the container digest, browser, and encoder environment.

## Official references

- [Core contract](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-core/SKILL.md)
- [CLI commands and references](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-cli/SKILL.md)
- [Registry](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-registry/SKILL.md)
- [Current documentation](https://hyperframes.heygen.com/introduction)
