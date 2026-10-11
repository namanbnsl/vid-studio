# Schedule

Research is scheduled per project. The schedule lives in the project's `studio.json` → `schedule`: `days` (`mon` … `sun`; all seven means every day) and `times` (`HH:MM`), in the project's `timezone`. Saving it does not run anything: a scheduled task in the user's agent app (or a local scheduler) has to send the research prompt at those times.

**Setting up or changing a schedule never runs research.** Only create, replace, or delete the task.

## Set up or change

The UI's Schedule dialog saves the schedule and copies a prompt like this one, which names the days, times, and timezone:

> Use the vid-studio skill to set up scheduled research for the project "Pipe Gyaan": weekdays at 07:00 and 19:00 (Asia/Kolkata). Create the scheduled task now, replacing any earlier one for this project. Don't run research now.

1. If the request came from chat rather than the UI, confirm the days, times, and timezone, then save them with `studio.py set-schedule --time 07:00 --time 19:00 --day mon … --timezone Asia/Kolkata` (leave out `--day` for every day).
2. Create the scheduled task. It sends this prompt, adding ` Workspace: /path` when the prompt you received named a workspace:

   > Use the vid-studio skill to run the scheduled research for the project "Pipe Gyaan".

   Use whichever option the user has:
   - **The agent app's scheduled tasks** (Claude, ChatGPT, Codex, and others). Create it in the user's project, at the given days and times. Use one task with several times if the app supports that, otherwise one task per time. The task must be able to reach the workspace folder, because it reads and writes files there.
   - **A local scheduler with a headless agent CLI** (cron, launchd, Task Scheduler). Show the user the exact line before installing it. Check the CLI's flags with `--help`. The machine has to be awake at those times. For weekdays at 07:00:

     ```cron
     0 7 * * 1-5 /path/to/claude -p "Use the vid-studio skill to run the scheduled research for the project \"Pipe Gyaan\"." --permission-mode acceptEdits --allowedTools "Bash(python3:*) WebSearch WebFetch Read Write Edit"
     ```
3. Remove any earlier scheduled task for the same project, so it doesn't run twice.
4. Reply with exactly what you created and when it next runs. If you can't create tasks here, give the user the exact steps and the prompt, and say that nothing is scheduled yet.

## Turn off

For "turn off scheduled research for the project …", delete that project's scheduled task(s), and run `studio.py set-schedule --off` if the schedule is still saved. Say what you deleted.

Never say a schedule is running unless you created it, or the user confirmed they did.
