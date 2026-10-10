# Vid Studio

One entry-point skill, `vid-studio`, for Codex, Claude Code, and compatible tool-capable agents to onboard and operate an ongoing local content studio. Start with your research interests and preferences, maintain profiles and monitors conversationally, review an inbox of findings, and choose what to produce. Research briefs, posts, scripts, and portrait videos are supported; video and WhatsApp copy are optional outputs.

The agent works with the capabilities you configure. This repository supplies instructions, local workspace templates, approval conventions, and setup/export helpers. It does not supply a scheduler or automatically connect research, voice, or media services. You can begin with research and monitoring and defer video tools until you want them.

## Install after pushing to GitHub

Push this repository to GitHub yourself, then replace `YOUR_USER/YOUR_REPO` with your GitHub repository:

```sh
npx skills add YOUR_USER/YOUR_REPO --skill vid-studio --agent codex claude-code
```

Run from the project in which you want the skill available. Add `--global` for a user-wide installation. You do not need to publish an npm package or manually register the repository on skills.sh. See the [official skills CLI instructions](https://github.com/vercel-labs/skills) for discovery and installation options.

To inspect discoverability before installing:

```sh
npx skills add YOUR_USER/YOUR_REPO --list
```

For local installation before pushing, use `./` in place of the GitHub repository.

## Onboard your studio

In Codex, select the skill or use `$vid-studio`. In Claude Code, use `/vid-studio` if your installed version exposes skills as slash commands, or explicitly ask it to use the installed Vid Studio skill.

> Use vid-studio to set up my studio at /absolute/path/to/my-studio. Start with research on Indian climate policy for non-specialists. Ask me about my preferences in short rounds. I want sourced briefs first; defer video setup. Present the setup proposal for approval before making changes.

Onboarding covers purpose, audience, research taste, editorial structure, brands, tools, data processing, budget, and monitoring. You can leave choices unresolved and return to them later. Review the proposal, approve its specified setup actions, then review completed setup before activation and content work. An existing workspace gets a proposed, non-destructive migration; new templates do not implicitly adopt new profiles or change approved projects.

## Set preferences and profiles

Research depth, source priorities, angles, tone, exact script structure, brand, motion, narration, music, and captions are customizable. Keep separate profiles for brands, audiences, or series, and use local template/reference files when useful. A script can have an exact section order with no hook.

> Create a science profile. Use this local script template exactly: finding, evidence, uncertainty, takeaway. No hook or CTA. Prefer primary sources and restrained motion.

> Clone science into a school audience profile with simpler language. Make science my default profile for future projects.

Preferences resolve from studio defaults → profile ancestors → selected profile → topic preferences → project overrides. Each project freezes its effective preferences and reference files for review. Later settings changes affect future projects; explicitly applying them to an active project creates a new snapshot and requires reapproval of affected stages. See [preferences and snapshots](skills/vid-studio/references/profiles.md).

## Manage monitors and your inbox

> Suggest sources and recurring topics for my climate profile, with reasons. Show them for review before enabling them.

> Add this feed as a weekly Monday 09:00 Asia/Kolkata monitor for the climate profile. Watch policy changes and exclude opinion pieces.

> Change that monitor to fortnightly. Pause the solar topic. Archive the old source and keep its findings.

> Show my inbox, rank new findings by relevance and novelty, and explain duplicates. Research the top candidate as a brief only.

Sources, topics, filters, profiles, and cadence remain editable. Recurring research saves evidence and signals locally; it can report no new relevant findings. Monitoring never implies producing or publishing content. Scheduling depends on an available host capability and approved scope; a local cadence setting alone does not create a running task. See [ongoing management](skills/vid-studio/references/manage-studio.md).

## Choose outputs, then produce content

Choose research-only, post-only, script-only, or full-video scope for each project. The bundled draft defaults list video and WhatsApp; they are editable suggestions, not required deliverables.

> Turn this finding into a sourced brief, then a script for the science profile. No WhatsApp copy or video.

> Make a portrait video from this approved script. Propose the deferred tool setup and storyboard for review.

For a full video, the applicable gates are topic → research plan → research → editorial → storyboard → assets → composition preview → rendered draft → export. Shorter scopes finish at their applicable gate. Every applicable stage requires explicit approval of its reviewed version before advancement. Revisions invalidate affected downstream approvals; a general production request does not preapprove later stages. Sending WhatsApp messages and publishing are separately authorized actions.

Local files hold settings, evidence, project snapshots, approvals, editable sources, and exports. Hosted processing follows your approved service/data policy. Approval records guide agent behavior; the helpers do not enforce approvals or advance stages.

## Portrait video with Hyperframes

Video production uses Hyperframes only: editable HTML/CSS scenes, seekable GSAP motion, local narration/media/data, Studio preview, and local MP4 rendering. The default is 9:16, 1080×1920, 30 fps; duration, design, voice, motion, and captions follow your profile within the portrait contract. A checked preview must be approved before encoding.

Read the [setup guide](docs/SETUP.md), [Hyperframes contract and setup](skills/vid-studio/references/hyperframes.md), [design and motion guidance](skills/vid-studio/references/design-motion.md), and [capability review and official sources](docs/HYPERFRAMES.md). Watch the [rendered portrait motion study](examples/portrait-motion-study.mp4) and review [validation evidence and limits](docs/VALIDATION.md). The starter is a silent technical motion study; a real episode still needs factual, creative, and audio review.

The installable entry point is [SKILL.md](skills/vid-studio/SKILL.md).
