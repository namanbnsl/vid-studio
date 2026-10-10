# Assets, video, and export

## Production assets gate

Read the approved project preference snapshot for narration/voice/pronunciation, music/SFX, captions, visual assets, motion, format and deliverables. Use the approved storyboard and scoped tool/service authorization. Read [hyperframes.md](hyperframes.md), [data-media.md](data-media.md), and [quality.md](quality.md). Hyperframes is the sole framework. Prefer local editable charts/diagrams and real assets when they support the explanation. Generated imagery is optional. Check the approved version's official tool instructions before invoking unfamiliar features.

Produce only selected assets: narration when narration.enabled is true, caption timing when captions.enabled is true, and the approved imagery, charts, fonts, music or effects. An intentionally silent profile can set narration.enabled false and disable music/SFX; captions can be disabled independently. Unresolved selections need review before production. Preserve editable chart sources and raw data. Narration must match the approved script; pronunciation or timing corrections that change wording need editorial reapproval. Material storyboard changes return to its gate.

`06-assets/manifest.json` records each asset's id, scene_ids, local_path, sha256, kind, source URL or generation provenance, license/usage terms, attribution, and any hosted service used. Generated assets include model/service and prompt where available. Never invent licenses. Unresolved rights or factual issues are blockers, not implicit approval.

Provide applicable asset contact sheets/keyframes, playable audio when selected, chart review, timing estimate, and manifest for approval before assembling the video.

## Composition preview gate

After assets approval, scaffold/edit Hyperframes sources under `07-video/hyperframes/`, using the approved frame.md and [design-motion.md](design-motion.md). Build portrait-native HTML scenes with local media, approved narration timing or silent reading holds, and seekable motion. Start with 9:16, 1080×1920, 30 fps only if setup approved those settings. Keep titles/captions away from target-platform UI overlays; validate safe areas against the intended destination. Do not claim one universal safe margin for all platforms.

Run applicable Hyperframes lint/check/keyframe diagnostics, inspect scene and boundary snapshots, and present the persistent reachable Studio preview with a source manifest and QA evidence. Do not encode merely because checks pass. Await explicit approval of the checked composition version before making a video draft. Studio edits invalidate the affected source approval.

## Video draft gate

After preview approval, encode the approved Hyperframes composition with the approved fps and `--quality looks`, preserving the output as a versioned draft. Record command/settings, environment, source hashes and render logs. This gate reviews the actual encoded output.

Review the actual render, including representative frames and full playback/audio where available. Check:

- Correct aspect ratio, resolution, fps, duration, and complete audio/video streams.
- No clipped text, missing fonts/media, layout collisions, misleading chart scales, or broken transitions.
- When selected: readable captions with correct names/numbers and synchronized narration. Always check sufficient reading time for displayed information.
- Clear voice, balanced music, no clipping, and appropriate loudness for the destination.
- Match to selected approved audio, scene order, evidence, brand, and asset manifest. Mark audio/caption checks not applicable only for intentionally disabled components; failed selected services remain blockers.

Use ffprobe or renderer metadata for technical checks if available. Record which checks were actually run in `07-video/qa.md`; visual/audio checks unavailable to the agent must be completed by user review. Do not mark an unperformed check as passed. Fix defects within the approved creative scope; changes to upstream content require reapproval. Present a playable draft, QA report, and revision notes. Await approval before creating final delivery outputs.

## Final export gate

After draft approval, use Hyperframes `--quality delivery` to produce the final video, plus captions where applicable, thumbnail/cover if approved, WhatsApp draft copy if requested, and `08-export/delivery.json` with paths, hashes, format, duration, attribution, and source-project revision. Use a broadly playable export profile appropriate to the approved destination (commonly MP4 with H.264/AAC); decode/inspect the final file, not just the preview. Follow quality.md for final playback/audio/technical verification.

Present the final delivery package for approval. Mark complete only after its explicit approval. Sending WhatsApp messages, uploading, or publishing is a separate scoped action requiring authorization; it is not included in export approval.

## Recovery

Cache successful artifacts and resume from the failed operation. Retry transient failures a small bounded number of times (normally at most two retries). Before retrying an external job, check whether it already exists/completed and whether repeating it would duplicate cost or uploads. On persistent failure, record the tool, error, preserved outputs, and available alternatives; stop dependent work.
