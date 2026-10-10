# Setup sequence

1. Install the skill with the command in the [README](../README.md). Select a separate local workspace.
2. Discuss audience, topics, research preferences, scripts, design, audio, outputs, monitors, tools, services, and costs.
3. Review the setup proposal. Approve the specified actions.
4. Let the agent create missing files and configure selected tools. Review and approve the completed setup.
5. Add, edit, or pause monitors. Review the inbox. Select a finding for research.
6. Approve topic, plan, research, and script or post, in sequence. Stop when the requested outputs are complete.
7. For video, approve storyboard, assets, preview, rendered draft, and final export, in sequence.

Leave undecided preferences open. Video setup can occur later. A schedule uses the actual host scheduler. Without a scheduler, collection is manual. Sending and publishing need separate approval.

## Local files

studio.json contains shared preferences, tools, and permissions. STATUS.md contains decisions, projects, and next actions. monitoring/ contains sources, topics, checkpoints, and findings. brand/frame.md contains video design instructions. Profiles are optional.

Each project contains its settings copy, references, research, scripts, assets, editable scenes, approvals, and exports. Create directories as necessary. Later studio changes apply to future work. Apply changes to active projects only when requested. Reopen affected stages.

## Tools

Use the agent's available research tools and scheduler. Voice, captions, music, generated assets, and WhatsApp outputs are optional. Do not change an unavailable selected service without approval.

Video uses Hyperframes only. HTML/CSS scenes support seeking, Studio preview, and MP4 render. The reviewed baseline uses Hyperframes 0.8.144 and GSAP 3.14.2. It requires Node.js 22+, usable Chromium, and FFmpeg/FFprobe.

Pin dependencies during approved setup. Disable telemetry by default. Advanced motion, imports, capture, and render remain available. Approve and test selected functions before use.

Read the [studio](../skills/vid-studio/references/studio.md), [research](../skills/vid-studio/references/research.md), [production](../skills/vid-studio/references/production.md), and [Hyperframes](../skills/vid-studio/references/hyperframes.md) guides as necessary.

## Verify setup

Try a small research brief first. Review preferences, templates, evidence, approvals, and resume behavior. Then try a short approved video with your selected design and audio.

The example video demonstrates the renderer. It does not validate your services or creative choices. Read the [test report](VALIDATION.md) for results and limits.
