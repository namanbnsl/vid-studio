# Hyperframes review and production

Vid Studio uses **Hyperframes only** to compose HTML scenes and render videos. The agent controls the workflow. Research, evidence, data, approvals, editable scenes, media, and outputs stay in the local workspace. Configure optional hosted processing separately.

## Review baseline

The review used official repository commit `affa4d53cf86334c18d0476955fce3f4f73f6a06`, published CLI `hyperframes@0.8.144`, and GSAP `3.14.2`. The source and published package versions agreed at the time of review. Separate orchestrator tasks reviewed the technical requirements and the quality of design, evidence, and audio. This pack does not include the upstream runtime or its complete skill catalog.

The review covered these areas:

- Request routing and composition requirements.
- CLI commands and command references.
- Creative direction, animation adapters, transitions, and keyframes.
- Registry components, media resolution, and audio.
- Explainer workflows, maps, and charts.
- Initialization effects, validation JSON, preview, and render.
- Optional methods to render videos and import designs.

Before an upgrade, read the installed version's help and source. Get approval for the change. Run the starter again. Run an episode affected by the change again.

## Video production

The studio can start with research and monitors. Configure the video tools when you select video production. Profiles and project overrides supply the editorial and design settings. See the setup outline.

1. Get approval for the local video tools, dependencies, and downloads. Include the brand, video design, format, and source scope. Include the selected voice service, budget, and processing policy.
2. Get approval for each stage in order. These stages include topic, research plan, sourced research, data, script, selected posts, and detailed portrait storyboard.
3. Get approval for the selected assets and their sources. Include narration and aligned captions when enabled. Include reading periods for silent videos and the selected charts and images.
4. Create Hyperframes scenes with local GSAP and fixed dependency versions.
5. Do browser, layout, contrast, and motion checks. Inspect sample frames and the editable Studio preview. Get preview approval before encoding.
6. Render a versioned `looks` draft. Review the decoded video and selected audio. Get approval for the `delivery` export.
7. Inspect the final delivery package. Get final approval. Get separate approval to publish it.

The starter is in `skills/vid-studio/assets/hyperframes-starter/`. It is a silent nine-second 1080×1920 example with three scene compositions. It shows information in stages, connector animation, clear typography, and a stable final message. It is not a researched episode. Do not apply it to every brand. Do not use it to replace narration or content review.

## Design requirements

Setup produces an approved `frame.md` for video design. It includes portrait examples for titles, explanations, and charts. Episode storyboards include actual keyframes and final chart states supported by sources. They also include explanatory motion, selected narration cues, caption positions, and sufficient reading time. Design the visual hierarchy and diagrams for portrait video. Do not shrink a wide slide into a phone frame.

Use motion to show relationships and direct attention. Do not invent changes in data over time. Do not animate quantitative marks beyond their correct values. Keep labels still when movement has no purpose. Do not move the background without a purpose.

Inspect reusable registry components. Adapt them to the approved brand and evidence. Clear visual explanations, correct data, and intelligible selected narration have priority over the number of effects, frame rate, or resolution.

## Capabilities and selection

### Core and modular compositions

Hyperframes supports main HTML files, timed clips, editor lanes, explicit layers, local scene templates, variables, media placement, and paused registered timelines. Each project has a fixed approved duration and unique IDs. Preserve clip visibility controlled by the runtime. Preserve media timing within each scene.

### Creative direction

The workflow supports video design specifications, style presets, typography, scene planning, story structure, visuals linked to sources, and review at phone size. Upstream design defaults are suggestions. Use approved branding and correct data when they conflict with those suggestions.

### Animation and keyframes

GSAP is the default animation system. Supported alternatives include CSS, WAAPI, Anime.js, Lottie, Three.js, shaders, and other adapters that support seeking. Use alternatives when the project requires them.

Specify each camera pose. Preserve the subject's identity during camera movement. Compare keyframe diagnostics with actual rendered frames. 3D and WebGL are optional. Verify GPU availability before you select them.

### Registry

Search for blocks and components by their intended function. Review downloads, save fixed local source copies, and record dependencies. Connect compositions and snippets correctly. Adapt landscape blocks to portrait layouts.

Replace sample figures. Inspect chart scales, included sounds, fonts, external dependencies, and licenses.

### Charts and maps

Use approved local datasets. Record the source of calculations. Use accurate fixed scales, labels, units, and uncertainty information. Store geography data locally.

Registry charts provide visual components. They do not validate evidence. Remove live API requests and CDN geography requests from render dependencies.

### Media, voice, and captions

Supported sources include local user assets, licensed media, authored diagrams, and optional generated media. Narration can use recordings, local services, or explicitly approved hosted services. Use the correct transcription language. Correct word and phrase timings.

An unavailable provider does not authorize a hosted alternative. Do not present generated illustrations as documentary evidence.

### Audio

Hyperframes supports separate voice, music, effect, and source tracks. It also supports audio groups, gain automation, audio effects, and optional voiceover carve or ducking. Measure loudness and true peak on the decoded export. Listen to the audio separately from numerical analysis. Music is optional.

### Validation and review

Run lint during authoring. Do browser, runtime, layout, motion, and contrast checks. Use motion sidecar files to specify the intended motion. Capture frames at scene boundaries, midpoints, and the final frame.

Review the video in Studio. Review encoded playback, complete decoding, FFprobe results, and audio measurements. An empty or skipped audit cannot pass. Static scenes with sufficient reading time are permitted.

### Website capture

Website capture is optional for demonstrations of actual websites or user interfaces. Do not use failed or blocked captures as output. A research URL does not require a website demonstration. It also does not require the website's design.

### Design import

Design import is optional. Sources include Figma, Open Design, and other supplied designs. Use existing exports and design tokens when available. Get separate approval for external account access and imports. Convert design states into explanatory motion. Do not use unexplained static slides as a substitute.

### Audio-reactive work and music-led work

Calculate waveform, frequency-band, or beat data locally when the brief requires it. Explainer narration usually controls pacing. Do not add live WebAudio or microphone dependencies to a deterministic export.

### Batches and variables

Use batches and variables for approved repeated layouts or versions. Fix the data and duration for each output. Keep approval records for each episode and version. A batch command does not approve all outputs.

### Transparent overlays, HDR, and shader transitions

These optional outputs require specific technical checks. Verify the format, GPU, alpha channel, and background layers. Use the approved portrait MP4 for standard explainer delivery unless the destination requires another format.

### Rendering

Local rendering is the default. Docker can make the environment more reproducible. Record the actual image digest, browser, and encoder. Do not promise identical bytes across different hosts.

Hosted cloud, AWS Lambda, and Google Cloud Run are optional Hyperframes execution methods. Get approval for upload scope, credentials, costs, and output retrieval. Installation of this pack does not deploy services to an account.

### Studio edits and history

Read the current editable project before you change it. Query stable context for selected elements when available. Preserve user changes. User changes invalidate affected reviewed hashes. Tool history helps recovery. It does not replace the workspace's approval record.

## Changes to upstream behavior

- Upstream workflows can combine approvals or run autonomously. Vid Studio keeps separate stage approvals. It requires preview approval before encoding.
- Some creative references suggest ambient movement. Explainers keep scenes still when the audience must read or understand evidence.
- Keep the labels and scales needed to interpret charts accurately.
- `init` can update skills and transcribe supplied media. Controlled setup disables implicit updates and transcription. Get separate approval for these capabilities.
- A fixed npm CLI version does not fix upstream skills or registry content. Record their versions separately.
- The default local workflow disables telemetry, automatic feedback, and public publishing. Describe approved downloads and model processing accurately.
- Doctor reports missing optional tools. Identify the checks required for the project. Use the project check to verify browser launch.
- Documentation can differ from source. Timing triggers and variable bindings are examples. Use the approved version's source, help, and observed checks. Record differences.

## Validation evidence

See [VALIDATION.md](VALIDATION.md) for completed tests and their limits. The starter and export helper have passed technical tests. An actual episode still needs audience, topic, voice, creative, factual, and audio reviews. The pack gives instructions to the agent. Its approval records are not an enforcement service.

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
