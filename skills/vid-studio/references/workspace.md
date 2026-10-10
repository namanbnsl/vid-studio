# Local artifacts and approval state

Use UTF-8 Markdown for reviewable documents and JSON for portable structured state. Paths inside the workspace are relative; timestamps use ISO 8601 with timezone. Credentials stay in the user's credential store/environment, never in research or manifests.

## Layout

```text
studio.json                      # policy/toolchain, defaults, default profile routing
ONBOARDING.md
profiles/<id>.json               # named tastes/brands/audiences, optional inheritance
settings/changes.json            # approved preference/monitor changes
settings/history/
setup-proposal.md
setup-approval.json
STATUS.md
brand/brand.md
brand/frame.md                    # approved video design and motion tokens
tools/                            # pinned toolchain, lockfile, capability report
monitoring/sources.json
monitoring/topics.json
monitoring/state.json             # mutable checkpoints; separate from approved config
monitoring/schedule.json          # only when configured
monitoring/inbox/                 # timestamped signals and collection reports
projects/<project-id>/
  project.json                   # selected profile/context and overrides
  preferences.json               # frozen effective settings and provenance
  preferences/rN.json             # immutable later preference revisions
  context/                       # copied brand/frame/script references + hashes
  approvals.json
  01-topic/topic.md
  02-plan/research-plan.md
  03-research/brief.md
  03-research/claims.json
  03-research/data/               # raw/derived datasets and chart specs
  03-research/sources/            # retrieved evidence and metadata
  04-editorial/script.md
  04-editorial/whatsapp.md
  05-storyboard/storyboard.md
  06-assets/manifest.json
  06-assets/                      # voice, fonts, imagery, chart data, etc.
  07-video/hyperframes/           # index.html, local assets, scene sources, frame.md
  07-video/                       # source manifest, preview approval, MP4, QA report
  08-export/                      # final video, captions, delivery manifest
  history/                        # prior versions and revision notes
```

Create project directories as needed. A project.json records schema_version, id, topic_id, source_id, profile_id, overrides, preferences_revision, preferences_path, angle, mode (one_off/recurring), active_stage, status (draft/awaiting_approval/approved/blocked/complete), revision, and updated_at. Topic recurrence belongs to the monitored topic, with separate project IDs for each episode. STATUS.md lists active projects, waiting gates, blockers, and the next action.

## Approval record

Workspace setup uses the same record shape as project approvals. Project `approvals.json` starts as `{"schema_version":1,"records":[]}`. Append a record for each explicit approval:

```json
{
  "stage": "editorial",
  "revision": 2,
  "decision": "approved",
  "approved_at": "2026-10-10T12:00:00+05:30",
  "approved_by": "user",
  "approval_message": "Approve script v2 and WhatsApp v2",
  "artifacts": [
    {"path": "04-editorial/script.md", "sha256": "<computed SHA-256>"},
    {"path": "04-editorial/whatsapp.md", "sha256": "<computed SHA-256>"}
  ],
  "depends_on": ["research:1"]
}
```

Compute real SHA-256 values using Python hashlib, sha256sum, or the host's equivalent. Hash every artifact required for the gate, including datasets/assets used in production. Use revision IDs for upstream dependencies; include the applicable operational setup revision and the approved project preference/context snapshot. Keep operational setup approvals separate from later profile/monitor change records. Record setup approvals for both the proposal and completed configuration. Only the completed setup authorizes project work.

Before transitioning, verify the hashes of all approved artifacts in the dependency chain. If files changed, append an invalidation event with stage, revision, reason, and timestamp. Preserve the original approval record. Mark that stage and descendants pending; approval is valid only if its latest decision is approved, hashes match, and all dependencies are valid. Projects depend on frozen settings/context, not live profile files. Future-only profile edits leave existing project approvals valid. Applying new preferences to an active project needs a reviewed snapshot revision and affected-gate invalidation. Changed operational permissions constrain all projects; reconcile setup approvals before continuing.

The `preview` stage approves the checked Hyperframes source tree and authorizes draft encoding. Its artifact list includes the source manifest, project frame.md, and QA/proof frames. `video` approves the resulting encoded draft and QA; `export` approves final delivery.

For large editable production trees, save a sorted path/hash manifest excluding caches and temporary files, and approve that manifest. Verify its listed file hashes on resume. Do not merely hash a manifest while ignoring subsequent changes to the files it lists.

## Review and handoff

Present links or absolute local paths to deliverables, a short summary, version, open issues, and the exact scope of approval. For video review, provide a playable video and selected frame previews. If playback tools are missing, give the file path and wait for the user's review.

An ambiguous “looks good” should be clarified if multiple gates or versions are pending. Approval can be a natural-language response identifying the presented version; no special command is required. Partial approval leaves the gate pending until every required deliverable is approved.

Save work before asking for approval. On switching agents, read the current artifacts and verify the state; do not trust a prior chat summary alone. Record actual tool/service provenance and failures. Do not overwrite existing files during setup or silently regenerate approved outputs.

These records guide agent behavior; they are not a security boundary against an agent or person bypassing the workflow. No separate enforcement service is included.

## Preference provenance

Follow profiles.md. Hash the selected immutable preference version and copied context manifest for project review. Resolver input hashes explain where settings came from; they are not live dependencies that invalidate frozen projects whenever another source is added. Only approved snapshot/context versions govern active creative work. For partial deliverables, record requested scope and completion at the last applicable reviewed gate.
