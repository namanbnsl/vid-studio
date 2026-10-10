# Validation evidence

Development tests were completed on 2026-10-10. Development test fixtures are not production episode approvals.

## Packaging and helpers

- The Skill Creator validator accepted the `vid-studio` frontmatter, name, and package.
- The official skills CLI discovered exactly one skill, `vid-studio`, from the local source in list-only mode. GitHub installation requires the user to push the repository first.
- JSON assets parse correctly. Local Markdown links resolve.
- Python helpers compile successfully. `python3 -m unittest discover -s tests -v` passes eleven behavioral tests. These tests include the customization checks below.
- The initializer creates a draft workspace without approval. Repeated runs preserve existing user edits. It rejects symlinks that redirect writes outside the selected workspace.
- The export helper verifies approved dimensions, frame rate, container duration, video duration, and frame coverage. It also verifies the required audio interval. Complete decoding is optional.
- Real FFmpeg test fixtures reject one-second video with three-second audio. They also reject three-second video with one-second audio. An explicitly approved shorter audio interval passes. The report still requires perceptual review.
- Hyperframes initialization was tested in a new temporary project. Implicit skill updates, transcription, and telemetry were disabled. Initialization created `AGENTS.md` and `CLAUDE.md`. These files were replaced with the vid-studio policy in that development project. The original files were saved separately.

## Hyperframes portrait starter

The tests used the official published runtime `hyperframes@0.8.144` and GSAP `3.14.2`. The environment used Node `24.21.0`, Chrome headless shell `151.0.7922.47`, FFmpeg `4.4.2`, and Linux x64. Capture used a software GPU. Runtime dependencies and test fixtures stayed in `/tmp` during development.

The starter's three modular scene files were tested with local GSAP:

- Lint processed four HTML files. It reported zero errors and zero warnings.
- The browser check returned `ok: true` and `browserSkipped: false`.
- Layout checks sampled 93 times. They reported zero errors and zero warnings.
- Motion checks sampled 181 states. Assertions for order, appearance, and position within the frame passed.
- Contrast checks sampled five times and tested 22 visible text elements. They reported zero errors and zero warnings.
- Keyframe enumeration completed. Representative frames from the hook, mechanism, and takeaway scenes were inspected.
- The delivery render produced 1080×1920 video at 30 fps. It contained 270 frames over nine seconds. The format was H.264/yuv420p. The video intentionally contained no audio.
- Software screenshot capture took approximately 42 seconds on the development machine. Performance depends on the machine and composition.
- Export inspection and complete decoding passed. The final encoded frame was inspected. It retained the completed takeaway without a black or reset final frame.

The repository includes [portrait-motion-study.mp4](../examples/portrait-motion-study.mp4). Its SHA-256 is `29e89796b193f95d2a98a2a5886a29aab1e0fcb1146101005a32478153edf8c4`.

## Audio integration fixture

A separate local synthetic tone tested a Hyperframes audio clip with an explicit ID and baseline gain. The 1.2-second render produced video and a non-silent audio stream. Stream coverage checks and complete decoding passed. The decoded mean volume was approximately -30.1 dB. The maximum volume was -26.8 dB.

These values show that audio mixing produced a non-silent output. They are not narration loudness targets or evidence of perceptual quality. The synthetic audio fixture is not included as content.

## Independent reviews

Orchestrator agents reviewed technical capabilities and the quality of creative work, evidence, and audio. They also reviewed the implemented pack. The final review identified three necessary changes:

- Replace generated upstream agent instructions.
- Verify duration for each export stream.
- Separate mutable monitor and schedule checkpoints from approved configuration hashes.

All reported findings were resolved. Stage approvals use agent instructions and local records. They do not use a separate enforcement engine.

## Remaining limits

The following work was not performed:

- Production of a real topic episode.
- Use of a speech or voice service.
- A complete human playback and listening trial.
- Schedule execution.
- An acceptance trial across agents in a new session.
- Use of a paid API.
- A cloud render or deployment.
- An external design import.
- Use of GPU, 3D, or HDR paths.
- Social publishing.

These optional capabilities are documented. They have not passed tests here. The first production episode still needs approved branding, research, narration when selected, and review at each stage.

## Customizable studio update

The pack includes schema-2 defaults and profiles. It also includes conversational onboarding, monitor management, context routing, project overrides, and immutable project preference snapshots.

Resolver tests verify these behaviors:

- Precedence for ancestor profiles, selected profiles, topics, and projects.
- Exact script structures without a hook.
- List replacement and clearing.
- Explicit null values and unknown custom fields.
- Read-only operation.
- Profile selection for sources, topics, and projects.
- Rejection of conflicting contexts, missing profiles, and cycles.
- Rejection of policy and renderer overrides.
- Preservation of version-1 settings after repeated initialization.
- Validation of portrait dimensions and frame rates.
- Deferred video settings.
- Rejection of profile symlinks that leave the workspace.
- Resume from saved preferences after live profile edits, with explicit immutable revisions.

The current helper suite passes eleven tests. This update did not change renderer files. The earlier render validation remains applicable. Complete onboarding and schedule execution still depend on the agent and approved capabilities.

## Simplified pack

The entry point routes to four guides: studio, research, production, and Hyperframes. Starter settings contain practical defaults. Optional profiles and custom fields remain supported.

Setup decisions and stage approvals use plain Markdown notes. These notes replace policy snapshots, change registries, and graphs of document dependencies. Helpers remain compatible with earlier, more detailed workspaces. Renderer sources and the tested Hyperframes requirements are unchanged.

## Technical writing

Documentation and templates now use ASD-STE100 writing rules. Agent instructions use the same rules for technical reports. Creative content uses the user's approved language and style.

A sentence-length scan found no prose sentence above 25 words. Local links and JSON files passed inspection. All 11 helper tests passed. The skill validator passed. These checks do not verify full dictionary compliance.
