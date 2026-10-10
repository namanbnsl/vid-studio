# Vid Studio

Vid Studio is one skill for an AI agent. It sets up a local research studio and prepares content for approval.

## Install

Push this repository to GitHub. Then run:

```sh
npx skills add YOUR_USER/YOUR_REPO --skill vid-studio --agent codex claude-code
```

For local installation, use `./` instead of the repository. Add `--global` for an installation for your user account.

## Start

> Use vid-studio. Set up my research studio at /path/to/studio.

The first invocation starts this sequence:

1. Learn your name, taste, language, audience, branding, and research interests.
2. Find and propose websites to monitor. Use available search, LLM tools, and optional Google Alerts inputs.
3. Find and propose topics from websites, LLM tools, and optional Google Trends data.
4. Recommend one-time or daily monitors from context. Configure approved schedules through the available host scheduler.
5. Break approved topics into questions and research them.
6. Verify claims with sources. Save research and evidence locally.
7. Generate a WhatsApp post and video script from approved research.
8. Include title, structure, script, visual strategy, charts, data, and proposed real assets.
9. Apply your edits and obtain approval. Stop at the approved post and script.

The agent prepares each next task proactively. You approve applicable stages before advancement. Preferences and monitors remain editable. Research-only output is also supported.

## Files and tools

[SKILL.md](skills/vid-studio/SKILL.md) is the entry point. The [studio guide](skills/vid-studio/references/studio.md) covers setup and monitors. The [research guide](skills/vid-studio/references/research.md) covers research, verification, posts, and scripts.

Shared settings live in studio.json. STATUS.md records progress. monitoring/ contains definitions, checkpoints, and findings. Each project keeps its preferences, evidence, outputs, and approval notes.

The agent uses your available tools and services. Alerts and Trends integrations are optional. A saved cadence is not a running schedule. Files stay local; external processing needs approval.

The workflow ends at approved posts and scripts. It does not produce videos, send posts, or publish content.

The two Python helpers create missing workspace files and resolve project preferences. They use the Python standard library.
