# Quality gates and review evidence

Read before presenting storyboard, assets, preview, rendered draft, or final export. Check output against the approved project preference snapshot and its custom research/script/brand/motion/audio rules, not a universal house style. Use the [QA template](../assets/project/qa.md). Quality is established by evidence and human review, not by claiming “cinematic” or selecting a large resolution.

## Blockers

Unsupported facts, misleading chart geometry, unresolved asset rights, missing media/fonts, illegible evidence/captions, broken language glyphs, unseekable motion, hidden live dependencies, unexplained black/reset frames, clipped/masked narration, and missing upstream approvals block advancement. Fix within the authorized stage or return to the affected earlier gate.

## Browser checks

Run the pinned Hyperframes `check --json --snapshots --at-transitions`. Require successful lint, actual browser execution (`browserSkipped: false`), nonzero sample coverage, and no unresolved errors. Inspect warning details and record their disposition. `--strict` can enforce a selected zero-warning policy, but intentional readable holds need judgment, not animated clutter.

Review images from every scene and transition, including meaningful intermediate poses and the last visible frame. Add checks at narration/chart/caption cue boundaries that the regular grid might miss. For important motion, use motion sidecars and focused keyframe proof shots; ensure selectors exist. A clean static linter or empty motion assertion set cannot prove animation quality.

## Evidence and design checks

Compare displayed copy, figures, rounding, scales, timestamps, caveats, and spoken meaning against approved claims and local chart specs. Ensure the image matches the claim (e.g. a forecast is visibly a forecast). Review the portrait at an approximation of phone size, including platform UI overlays. Verify typography hierarchy, glyphs, reading holds, caption collision, source-note clarity, consistency of series colors, and continuity between related scenes.

## Playback and audio checks

After preview approval authorizes encoding, inspect the actual rendered draft, not just the browser:

Apply sound/listening and caption synchronization checks only to selected components. Record intentionally absent components as not applicable, and selected but failed components as failed. A silent video still needs complete visual playback review.

1. Normal playback with sound when present: rhythm, explanation, narration/caption synchronization, glitches, and transitions.
2. Muted playback: visual argument, captions, data labels, and readable holds.
3. Audio-only when present: natural narration, pronunciation, factual numbers, clipping, intelligibility, and music/effect balance.

Record performed, failed, and user-pending checks separately. If the agent cannot hear or play video, it must provide the actual file and request the corresponding user review. Never mark listening passed based on waveform analysis alone.

Use ffprobe for streams, dimensions, fps, codec/pixel format, duration, and audio presence. Decode the full file with FFmpeg to detect corrupted/truncated output; account for frame/sample rounding when comparing duration. Measure loudness/true peak if audio is present. Inspect boundary and final frames from the encoded file as well as Hyperframes snapshots. Keep log summaries, tool versions, settings, and file hashes with QA.

The bundled helper produces a technical JSON report and nonzero exit on mismatches:

```sh
python3 <skill-directory>/scripts/verify_export.py <video.mp4> --width 1080 --height 1920 --fps 30 --duration <approved-seconds> --require-audio --decode
```

Use the approved settings and omit `--require-audio` only for intentionally silent outputs. It does not measure loudness, inspect facts/design, or approve playback/listening. Those checks remain separate.

The helper checks picture-stream coverage separately from container duration. Required audio normally covers the full video; for an approved shorter or offset audio interval, use `--audio-start` and `--audio-duration` explicitly. Unknown stream coverage fails rather than passing. A complete mixed-audio stream does not prove complete narration: verify narration-source duration/timing against the approved script at assets review and listen to the output.

## Approval and revisions

Present the latest deliverables and their version, explain defects/intentional exceptions and the requested transition. Preview approval identifies the checked source tree; rendered-draft approval identifies the MP4 and QA report. Any Studio edit, chart/data change, script change, or asset replacement invalidates affected approvals. Preserve revision history and regenerate dependent checks. Final delivery must be verified even when it uses the same source as the approved draft, because encode settings and output files changed.

## Definition of ready

Ready for preview review: approved upstream content/assets, complete editable composition, passed applicable browser checks, inspected proof frames, reachable Studio URL, and an explicit list of unperformed checks.

Ready for draft review: preview approved, actual draft file verified, applicable playback/audio checks documented, and no unresolved technical/factual defect.

Ready for completion: draft approved, final delivery decoded/inspected, necessary rights/attribution included, reviewed source/environment recorded, and final package explicitly approved. Publishing remains separate.
