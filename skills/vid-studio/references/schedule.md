# Daily schedule

Research is scheduled per channel. The times are saved in the channel's `studio.json` → `schedule.times`, and the user sets them in the UI's Schedule dialog. Saving the times does not run anything: something has to send the prompt at those times. Each channel's scheduled run sends a prompt naming that channel:

> Use the vid-studio skill to research now for the channel "Pipe Gyaan". This is a scheduled run.

(The UI adds the workspace path when it isn't the default one.) With several channels, create one scheduled task per channel.

Set it up in whichever option the user has. Confirm the exact times before creating anything.

- **The agent app's scheduled tasks.** Many agent apps (Claude, ChatGPT, Codex and others) can run a prompt on a schedule. Create one daily task per time in the user's project. The task must be able to reach the workspace folder, because it reads and writes files there. If you can create the task yourself, do so and report what you created; otherwise, give the user the exact steps.
- **A local scheduler with a headless agent CLI.** This works with cron, launchd, or Task Scheduler. Example cron line (check the CLI's flags with `--help`):

  ```cron
  0 7 * * * /path/to/claude -p "Use the vid-studio skill to research now for the channel \"Pipe Gyaan\". This is a scheduled run." --permission-mode acceptEdits --allowedTools "Bash(python3:*) WebSearch WebFetch Read Write Edit"
  ```

  Show the user the exact line before installing it. The machine has to be awake at that time.

Never say a schedule is running unless you created it, or the user confirmed they did.
