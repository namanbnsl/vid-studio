# Validation evidence

Performed during pack development on 2026-10-10. Development fixtures are not production episode approvals.

## Packaging and helpers

- Skill Creator validator: valid `vid-studio` frontmatter/name/package.
- Official skills CLI, local source in list-only mode: discovered exactly one skill, `vid-studio`. GitHub installation cannot be tested until the user pushes the repository.
- JSON assets parse; local Markdown links resolve.
- Python helper compilation passes. `python3 -m unittest discover -s tests -v`: eleven behavioral tests pass (including the customization checks below).
- Initializer creates draft/unapproved workspace, keeps existing user edits on repeated runs, and rejects a symlink that redirects writes outside the selected workspace.
- Export helper checks approved dimensions, fps, container and picture-stream duration/frame coverage, required audio interval, and optional full decode. Real FFmpeg regression fixtures reject one-second picture with three-second sound and the reverse; an explicitly approved shorter audio interval is accepted. Perceptual review remains pending in the report.
- Hyperframes init was exercised in a fresh temporary scaffold with implicit skills/transcription/telemetry disabled. Its generated AGENTS.md/CLAUDE.md were confirmed and replaced with the vid-studio policy in that development scaffold, saving originals separately.

## Hyperframes portrait starter

Official published runtime: `hyperframes@0.8.144`; GSAP `3.14.2`. Node `24.21.0`, Chrome headless shell `151.0.7922.47`, FFmpeg `4.4.2`, Linux x64 software-GPU capture. Runtime dependencies and fixture work stayed in /tmp during development.

The shipped starter's three modular scene files were tested with local GSAP:

- Lint: four HTML files, zero errors or warnings.
- Browser check: `ok: true`, `browserSkipped: false`.
- Layout: 93 sampled times, zero errors or warnings.
- Motion: 181 sampled states, ordering/appearance/in-frame assertions pass.
- Contrast: five sample times, 22 visible text checks, zero errors or warnings.
- Keyframe enumeration completed. Representative hook, mechanism, and takeaway snapshots were inspected.
- Delivery render: 1080×1920, 30 fps, nine seconds, 270 frames, H.264/yuv420p, intentionally no audio. Software screenshot capture completed in about 42 seconds on this development machine; performance varies by machine/composition.
- Export inspection and complete decode passed. The encoded final frame was inspected and retained its completed takeaway rather than a black/reset tail.

The repository includes [portrait-motion-study.mp4](../examples/portrait-motion-study.mp4). SHA-256: `29e89796b193f95d2a98a2a5886a29aab1e0fcb1146101005a32478153edf8c4`.

## Audio integration fixture

A separate local synthetic tone tested an identified Hyperframes audio clip with baseline gain. The 1.2-second render produced video and a real non-silent audio stream; stream-coverage checks and full decoding passed. Decoded mean volume measured approximately -30.1 dB and maximum -26.8 dB. These values demonstrate non-silent mixing, not a narration loudness target or perceptual quality claim. The synthetic audio fixture is not shipped as content.

## Independent reviews

Orchestrator subagents reviewed technical capabilities, creative/evidence/audio quality, and the implemented pack. The final review found and prompted fixes for generated upstream agent instructions, per-stream export duration verification, and separation of mutable monitoring/schedule checkpoints from hashed approved configuration. All reported findings were addressed. Approval gates are agent instructions with local records, not a separate enforcement engine.

## Remaining limits

No real topic episode, speech/voice service, full human playback/listening trial, schedule execution, cross-agent fresh-session acceptance trial, paid API, cloud render/deployment, external design import, GPU/3D/HDR path, or social publishing was performed. Those optional capabilities are documented, not claimed tested. A first production episode still needs the user's approved branding, research, narration, and review at every gate.

## Customizable studio update

Schema-2 defaults/profiles, conversational onboarding and monitor management, context routing, per-project overrides, and immutable project preference snapshots are now included. New resolver tests verify ancestor/profile/topic/project precedence, exact no-hook script structures, list replacement/clearing, explicit null values, unknown custom fields, read-only behavior, source/topic/project profile selection, conflicting contexts, missing profiles, cycles, policy/renderer override rejection, preserving version-1 settings after repeat initialization, portrait dimensions/frame rates, deferred video settings, profile symlink escapes, and frozen resume after live profile edits with explicit immutable revisions. The current eleven-test helper suite passes. No renderer files changed in this update, so the earlier render validation remains applicable. End-to-end onboarding/scheduler behavior still depends on the host agent and approved capabilities.
