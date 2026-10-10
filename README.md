# Vid Studio

Vid Studio is one skill for an AI agent. The agent sets up a local studio for explainer content.

The agent saves your preferences, monitors sources and topics, does research, and writes scripts and posts. Hyperframes produces vertical videos. You approve each applicable stage before the agent starts the next stage.

## Install

Push this repository to GitHub. Then run this command:

```sh
npx skills add YOUR_USER/YOUR_REPO --skill vid-studio --agent codex claude-code
```

For a local installation, use `./` instead of the GitHub repository. Add `--global` for an installation that applies to your user account.

## Start

> Use vid-studio. Set up my studio at /path/to/studio. Ask me about my research and script preferences.

You can then give these instructions:

- “Monitor these websites each week. Research battery policy each day.”
- “Use this script template exactly. Do not add a hook or CTA.”
- “Create another brand profile. Use these reference examples.”
- “Pause this topic. Show my inbox. Put the most relevant findings first.”
- “Research this topic. Produce a brief only.”
- “Make a vertical video from this approved script. Use slow motion and simple transitions.”

You can change the research, script structure, visuals, motion, voice, captions, and outputs. The studio saves shared preferences in studio.json. Profiles are optional. Each project saves its own preferences. Research can start before video setup.

## Files

- [SKILL.md](skills/vid-studio/SKILL.md) gives the entry instructions and approval rules.
- The [studio guide](skills/vid-studio/references/studio.md) gives instructions for setup, preferences, monitors, and schedules.
- The [research guide](skills/vid-studio/references/research.md) gives instructions for evidence, scripts, and posts.
- The [production guide](skills/vid-studio/references/production.md) gives instructions for design, assets, and quality reviews.
- The [Hyperframes guide](skills/vid-studio/references/hyperframes.md) gives renderer instructions and technical requirements.
- scripts/ contains helpers for setup, preferences, and export checks.
- assets/ contains templates and an editable example video.

The [setup outline](docs/SETUP.md) gives the full sequence. The [Hyperframes review](docs/HYPERFRAMES.md) gives the available functions. The [example video](examples/portrait-motion-study.mp4) shows motion. The [test report](docs/VALIDATION.md) gives results and limits.

The agent uses your available research tools, scheduler, and services. The pack does not include these services. Files stay local. External services process data only with your approval. Approval notes guide the agent. They do not enforce the rules through software.
