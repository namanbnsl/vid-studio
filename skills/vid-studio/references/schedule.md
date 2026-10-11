# Daily routine and scheduling

## The daily routine

Run this whenever the prompt says "run the daily routine", whether from a scheduler or from the user. Never ask questions during it. Stop at review gates.

1. Run `studio.py status`. If setup is incomplete, write a digest saying so and stop.
2. **Scan.** Do Scan and Triage from [discover.md](discover.md#scan).
3. **Daily topics.** For each one due, follow [research.md](research.md#0-start-or-resume): either run `no-news`, or create a project and research it.
4. **Once topics.** Research active once topics with no project yet.
5. **Limit.** Start at most `automation.max_projects_per_run` new projects in total. Any that don't fit wait until tomorrow; take the most timely first.
6. **Write.** For each project that reaches `writing`, draft the script and post ([write.md](write.md)) and move it to `script-review`.
7. **Propose topics.** Add up to 3 proposed topics from triage. They wait for approval if `review.topics` is true.
8. **Digest.** Write `digests/<date>.md`:
   - **Waiting for you:** scripts to review, topics to approve, and the Alerts the user should create.
   - **New today:** projects created (title + one-line summary), plus no-news topics with their reason.
   - **Inbox highlights:** 3-5 stories.
   - **Problems:** failed feeds, failed fetches, and missing tools.

   End by printing the "Waiting for you" section.

## Choosing a scheduler

The data lives on the user's machine, so the scheduled agent must run where it can read and write the workspace. Check what the current host offers, recommend one option, and confirm the exact schedule with the user before creating anything. Afterwards record it in `studio.json` → `schedule`: `description` like "daily 07:00 Asia/Kolkata via cron + claude", `host`, and `task_id` if there is one.

The prompt for every scheduler is:

> Use the vid-studio skill. Run the daily routine.

### Option A: OS scheduler + a headless agent CLI (recommended, fully local)

Works with any agent CLI that has the skill installed. Find the CLI path with `which claude` / `which codex`, and check its flags with `--help`, because they change between versions. Examples (07:00 daily):

```cron
# crontab -e   (Linux, macOS, WSL)
0 7 * * * cd "$HOME/vid-studio" && /path/to/claude -p "Use the vid-studio skill. Run the daily routine." --permission-mode acceptEdits --allowedTools "Bash(python3:*) WebSearch WebFetch Read Write Edit" >> "$HOME/vid-studio/digests/cron.log" 2>&1
0 7 * * * /path/to/codex exec -C "$HOME/vid-studio" --sandbox workspace-write -c sandbox_workspace_write.network_access=true "Use the vid-studio skill. Run the daily routine." >> "$HOME/vid-studio/digests/cron.log" 2>&1
```

- Cron uses the machine's timezone and a minimal `PATH`, so use absolute paths. Set `VID_STUDIO_HOME` in the line if the workspace is not `~/vid-studio`.
- The agent needs web access. Give it the minimum permissions that let it run `python3`, search, fetch, and edit files in the workspace.
- On macOS you can use launchd instead; on Windows, Task Scheduler running the same command.
- The machine must be awake at that time.

To install, show the user the exact line. After they confirm, append it with `(crontab -l 2>/dev/null; echo "LINE") | crontab -`. Then run the routine once by hand to prove it works.

### Option B: the host app's own scheduled tasks

Some desktop agent apps offer scheduled or automated tasks that run locally with file access. If you have such a tool, create a daily task with the prompt above and the workspace as its working folder. Record the returned task ID.

Some in-session tools only fire while that chat session is open. Examples are a `/loop` command or session cron tools. Use them only for short-lived monitoring and tell the user about the limitation.

### Option C: cloud schedulers (ChatGPT Tasks, cloud routines)

These run on the provider's servers and cannot see the local workspace. Use them only if the user accepts one of these:

- The workspace is a private git repo the cloud agent can clone and push to. The user then pulls the results.
- The task only does discovery ("list today's top stories on X with links"). The user pastes the result into a local session, which runs triage.

Never describe a cloud task as updating local files when it cannot.

## Changing or stopping the schedule

Edit or remove the actual scheduler entry (crontab line, task ID). Then update `studio.json` → `schedule`. If you cannot reach the scheduler, tell the user exactly what to change.
