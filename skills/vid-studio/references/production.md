# Produce and review video

Read the saved project preferences, approved script, and copied design references. Use Hyperframes only. Follow hyperframes.md for setup, technical requirements, and advanced functions.

The default format is 1080×1920 at 30 fps. Apply the approved 9:16 dimensions, frame rate, and duration.

## Storyboard

Save the storyboard under 05-storyboard/. Show a portrait keyframe for each scene. Show a static final state and specification for each data graphic.

Include scene ID, estimated times, claim IDs, visible text, selected audio and captions, layout, motion, and reading holds. Include the asset plan, costs, and services. Review the design at phone size. Include destination interface overlays.

Apply the user's visual references, fonts, colors, and motion preferences. Keep one clear explanatory focus for each beat. Use motion to explain mechanisms, comparisons, or relationships. Then hold the image for sufficient reading time.

Do not animate chart values beyond their correct positions. Do not imply chronology without time data. Keep object identity and continuity. Avoid effects that distract from the explanation.

Charts need correct scales, units, labels, caveats, source notes, and approved values. Keep calculations reproducible. Show missing values as missing. Identify illustrative samples. Identify generated images if users could mistake them for evidence.

Select editable diagrams, charts, licensed assets, or generated images for their explanatory purpose. Get storyboard approval before final narration, paid assets, or generated production assets.

## Assets

Create selected components under 06-assets/. Narration, captions, music, sound effects, and generated images are optional. For silent video, use reading holds. If captions are disabled, transcription is not required.

If a selected service fails, report the failure. Do not disable the component or change providers without approval.

For narration, use approved recordings, local TTS, or authorized external services. Review a voice sample, pronunciations, and number reading. Keep the approved meaning and words. If the words change, return to editorial review.

Measure narration duration. Derive scene, word, and phrase times from the actual audio. Select the correct transcription language and model when necessary. Correct transcription errors against the approved script. Word count does not give final alignment.

Keep narration, music, effects, and source audio separate. Mute source audio when you replace it. Use documented Hyperframes audio groups, gain, envelopes, effects, and ducking. Local fonts need usage rights, correct weights, styles, and glyphs.

Review captions for names, numbers, phrase groups, timing, and phone readability. Save an asset manifest. Record paths, scene IDs, hashes, sources, usage rights, and attribution. For generated assets, record the service, model, and prompt when available.

Keep editable chart sources and raw data. Do not invent licenses. Show applicable asset previews, charts, audio, timing, and manifest for approval. Wait for approval before assembly.

## Composition preview

Build the composition under 07-video/hyperframes/. Use local dependencies and motion that supports seeking. Copy the approved frame.md into the composition. Use actual audio timing or approved silent reading holds. Keep selected captions clear of destination overlays. Preserve correct chart final states.

Run the pinned Hyperframes checks. Inspect scene, transition, and final-frame images. Require successful lint, browserSkipped: false, sufficient sample coverage, and no unresolved errors. Record warnings and their resolution.

Add focused timing and keyframe checks where necessary. Empty assertions do not prove motion quality. Use hyperframes.md for commands and motion sidecars.

Show the reachable Studio preview, proof frames, and review notes. Keep the preview available during review. Save a sorted path/hash manifest for source files, dependencies, and assets. Exclude caches and temporary files.

Get approval for the checked source version before draft encoding. If Studio edits change files, repeat the checks and affected review. On resume, compare actual files with the manifest. A manifest hash alone does not prove that its files are unchanged.

## Rendered draft

After preview approval, render with quality looks. Review the actual MP4 for these items:

- Facts, chart geometry, labels, and glyphs.
- Phone readability, brand, motion continuity, and reading holds.
- Unexplained black frames or reset frames.
- Selected narration, captions, pronunciation, and audio balance.
- Dimensions, frame rate, codecs, pixel format, duration, and audio coverage.
- Complete FFmpeg decode, boundary frames, and the final frame.

Do a full visual playback review. When audio is present, listen for clipping and intelligibility. Measure loudness and true peak against the approved target. Audio measurements do not replace listening.

```sh
python3 <skill-directory>/scripts/verify_export.py <video.mp4> --width 1080 --height 1920 --fps 30 --duration <approved-seconds> --require-audio --decode
```

Use the approved settings. For intentional silence, omit --require-audio. For an approved shorter or offset audio interval, use --audio-start and --audio-duration.

The helper measures video and audio coverage separately. Container duration cannot hide a truncated stream. Mixed audio coverage does not prove complete narration. Inspect the narration source and listen to the output.

Use qa.md to record completed, failed, user-pending, or inapplicable checks. Record tools, versions, and actual outputs. If playback is unavailable, ask the user to review the file. Do not report an unperformed check as passed.

Unverified facts, unresolved rights, missing files, illegible text, broken seeking, or missing approval prevent advancement. Get draft approval before final export.

## Final export

Render quality delivery to a new final path. Inspect the final file too. Supply selected caption, cover, and post files. Include attribution and delivery.json. Record paths, hashes, format, duration, and source version.

MP4 with H.264/AAC is a common delivery format. Use the format for the approved destination. Present the package for final approval. Get separate approval to publish or send it.

Revisions reopen the earliest affected stage and later stages. Keep earlier reviewed files and approved evidence. Approval notes guide the agent. They are not a software enforcement service.
