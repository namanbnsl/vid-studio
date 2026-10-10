---
name: vid-studio
description: Set up and operate a local explainer studio with user preferences, source monitors, research, scripts, posts, and approved Hyperframes vertical videos.
---

# Vid Studio

Operate the studio through conversation. Save the user's preferences locally. Use the available agent tools. Use Hyperframes for video production. Keep videos vertical, with a 9:16 aspect ratio.

## Select the guide

Read studio.json and STATUS.md if these files exist. Select the guide for the request:

- Setup, preferences, brands, monitors, inbox, or schedules: [studio.md](references/studio.md).
- Topics, research, scripts, or posts: [research.md](references/research.md).
- Storyboards, assets, preview, render, or quality review: [production.md](references/production.md).
- Hyperframes setup, technical requirements, or advanced functions: [hyperframes.md](references/hyperframes.md).

Do not start a video from a management request. Stop when the user approves the requested outputs. WhatsApp posts, narration, captions, music, and generated images are optional.

## Write clearly

Use [ASD-STE100](https://www.asd-ste100.org/faq.html) for technical instructions and status reports. Use short sentences with one topic. Use the imperative for instructions. Use a maximum of 20 words per instruction and 25 words per description. Use consistent technical names. Keep commands and code identifiers unchanged. For creative content, use the user's approved language and style.

## Operate the studio

- Ask setup questions in short groups. Save preferences in studio.json. Use instructions and local examples instead of unnecessary fields. Add profiles only when useful.
- Copy the effective preferences and applicable references into each new project. Use that copy when you resume the project. Apply later preferences only when requested.
- Prepare each applicable stage. Show the actual output. Wait for approval before the next stage.
- Use this sequence: setup → topic → plan → research → script/post → storyboard → assets → preview → rendered draft → final export.
- Record the current stage, approved versions, and next action in STATUS.md and the project's approvals.md.
- If an approved output changes, reopen the affected stage and later stages. Keep earlier approved work.
- Keep settings, evidence, and outputs in local files. Use only approved services, downloads, and costs. Get separate approval to send or publish outputs.
- Support factual claims and charts with evidence. Cross-model review is optional and initially disabled.
- Keep user edits. Report tools that are unavailable and operations that fail.

A request for production does not approve later stages. A schedule does not approve project outputs. Local storage does not mean local processing.

The Python helpers create missing files, resolve preferences, and inspect exports. The helpers do not approve work or provide external services.
