#!/usr/bin/env python3
"""Try vid-studio quickly while developing it (not part of the installed skill).

  python3 dev.py demo                 throwaway studio with sample data, opened in the browser
  python3 dev.py sandbox [--seed]     test project with the skill linked (edits apply instantly)
  python3 dev.py try research         run an agent headlessly in the sandbox, then show what changed
  python3 dev.py reset                wipe the sandbox's studio data
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parent
SKILL = REPO / "skills" / "vid-studio"
STUDIO_PY = SKILL / "scripts" / "studio.py"
DEMO = Path(tempfile.gettempdir()) / "vid-studio-demo"
SANDBOX = REPO.parent / "vid-studio-sandbox"

sys.path.insert(0, str(STUDIO_PY.parent))
import studio  # noqa: E402

PROMPTS = {
    "setup": ("Use the vid-studio skill to set up a channel called \"Test Plumbing\": Indian plumbing and bathroom products "
              "for homeowners and dealers, in Hinglish, timezone Asia/Kolkata. Don't ask me anything: choose 4 topics and "
              "about 6 sources yourself, add the sources as suggestions, and open the studio."),
    "research": "Use the vid-studio skill to research now for the channel \"{channel}\".",
    "draft": "Use the vid-studio skill to write the draft for the script \"{script_title}\" ({script}) in the channel \"{channel}\".",
    "status": "Use the vid-studio skill: what's new in the channel \"{channel}\"?",
}


def run_studio(home: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run([sys.executable, str(STUDIO_PY), "--workspace", str(home), *args],
                            capture_output=True, text=True)
    if check and result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    return result.stdout.strip()


def serve(home: Path, open_browser: bool) -> None:
    url = run_studio(home, "serve", "--background").split()[-1]
    print(f"Studio: {url}")
    if open_browser:
        webbrowser.open(url)


# ---------------------------------------------------------------- sample data

def seed(home: Path) -> None:
    """Two channels with topics, sources, a finished run, findings, and scripts."""
    (home / "channels").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SKILL / "assets" / "README.md", home / "README.md")

    folder = studio.create_channel(home, "Pipe Gyaan", "Plumbing, sanitaryware और bathroom की हर बात, आसान भाषा में।", "Hinglish")
    pipe = studio.Studio(folder, home)
    pipe.update_settings({"audience": "Indian homeowners, plumbers and dealers", "timezone": "Asia/Kolkata",
                          "schedule": {"times": ["07:00"]}})
    for name, description in [("PVC pipes", "Prices, launches, BIS standards."), ("CP fittings", "Taps, showers, sensor faucets."),
                              ("Tiles", "Prices, duties, new ranges."), ("Water tanks", "Storage, hygiene, new products.")]:
        pipe.add_topic(name, description)
    pipe.add_source("https://www.supreme.co.in/news", "Supreme Industries")
    pipe.add_source("https://www.jaquar.com/news", "Jaquar")
    pipe.add_source("https://www.bis.gov.in", suggested_reason="BIS standards for pipes and fittings are published here first.")
    run, _, _ = pipe.start_run()
    pipe.add_findings(run["id"], [
        {"title": "Supreme launches a new CPVC pipe range", "summary": "A new range for hot water lines, rated up to 93°C.",
         "topics": ["PVC pipes"], "sources": [{"url": "https://www.supreme.co.in/news/cpvc-launch", "publisher": "Supreme Industries"}]},
        {"title": "Jaquar launches a new series of smart sensor faucets", "summary": "Touchless faucets now start at ₹6,500 and use about 50% less water.",
         "topics": ["CP fittings"], "sources": [{"url": "https://www.jaquar.com/news/sensor", "publisher": "Jaquar"},
                                               {"url": "https://www.financialexpress.com/jaquar", "publisher": "Financial Express"}]},
        {"title": "DGTR opens anti-dumping probe into vitrified tiles", "summary": "The probe covers tiles imported from China; domestic prices could rise.",
         "topics": ["Tiles"], "sources": [{"url": "https://www.dgtr.gov.in/tiles-2026", "publisher": "DGTR"}]},
    ])
    pipe.mark_checked(run["id"], run["sources"], "sample check")
    pipe.finish_run(run["id"])
    sensor = next(f for f in pipe.findings() if "Jaquar" in f["title"])
    script = pipe.create_script("Sensor taps: पैसा बचेगा या नहीं?", [sensor["id"]])
    pipe.update_script(script["id"], {
        "script": ("## HOOK (5s)\nएक नल जो छूने की ज़रूरत ही नहीं — पर क्या ये **पानी और पैसा** बचाता है? [1]\n\n"
                   "*Visual:* tap close-up\n\n## CONTEXT (15s)\nJaquar के नए sensor faucets ₹6,500 से शुरू। [1]\n\n"
                   "- Touchless, battery से चलते हैं\n- पानी की खपत लगभग 50% कम\n\n*Visual:* price card\n"),
        "post": "*Sensor taps: पैसा बचेगा?*\n\nJaquar के नए sensor faucets ₹6,500 से शुरू। [1]\n\nhttps://www.jaquar.com/news/sensor\n",
        "notes": ("# Research notes\n\n## What's new\n- Jaquar's touchless range starts at **₹6,500**. [1]\n"
                  "- The 50% water saving is the maker's claim; no independent test yet.\n\n"
                  "## Sources\n1. Jaquar, Sensor faucets, https://www.jaquar.com/news/sensor\n")})
    pipe.create_script("Water tank को साफ़ कैसे रखें", topic_ids=["water-tanks"])

    folder = studio.create_channel(home, "Explained in 90s", "Indian tech and money news, explained in 90 seconds.", "English")
    news = studio.Studio(folder, home)
    news.add_topic("UPI & payments", "Fees, NPCI rules, fraud, new features.")
    news.add_source("https://rbi.org.in", "Press releases")
    run, _, _ = news.start_run()
    news.add_findings(run["id"], [{"title": "RBI raises UPI Lite wallet limit to ₹5,000",
                                   "summary": "Higher per-payment cap and wallet balance from November 1.", "topics": ["UPI & payments"],
                                   "sources": [{"url": "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=61234", "publisher": "RBI"}]}])
    news.mark_checked(run["id"], run["sources"], "1 press release")
    news.finish_run(run["id"])


# ---------------------------------------------------------------- commands

def cmd_demo(args) -> None:
    if DEMO.exists():
        run_studio(DEMO, "serve", "--stop", check=False)
        shutil.rmtree(DEMO)
    seed(DEMO)
    print(f"Demo studio with sample data: {DEMO}")
    serve(DEMO, not args.no_open)


def link(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        raise SystemExit(f"{target} is a copied install (from `npx skills add`?). Remove it first so the sandbox can link to your working copy.")
    target.symlink_to(SKILL, target_is_directory=True)


def cmd_sandbox(args) -> None:
    root = Path(args.path).expanduser().resolve()
    home = root / "studio"
    root.mkdir(parents=True, exist_ok=True)
    # Linked, not copied: Claude Code reads .claude/skills, Codex and others read .agents/skills.
    link(root / ".claude" / "skills" / "vid-studio")
    link(root / ".agents" / "skills" / "vid-studio")
    settings_path = root / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    settings.setdefault("env", {})["VID_STUDIO_HOME"] = str(home)  # keep test data away from ~/vid-studio
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    note = (f"# vid-studio test sandbox\n\nThe studio for this project lives at `{home}`. "
            f"Always pass `--workspace {home}` to studio.py (or set VID_STUDIO_HOME to it).\n")
    for name in ("AGENTS.md", "CLAUDE.md"):
        (root / name).write_text(note)
    if args.seed and not studio.channel_dirs(home):
        seed(home)
    print(f"Sandbox: {root}\nStudio data: {home}\nThe skill is linked to {SKILL}, so edits apply immediately.\n")
    print(f"Try it:\n  cd {root} && claude          # then: Use vid-studio to set up my channel\n"
          f"  python3 {Path(__file__).name} try setup      # or run it headlessly")


def cmd_try(args) -> None:
    root = Path(args.path).expanduser().resolve()
    home = root / "studio"
    if not (root / ".claude" / "skills" / "vid-studio").exists():
        raise SystemExit(f"No sandbox at {root}. Run: python3 {Path(__file__).name} sandbox")
    prompt = " ".join(args.prompt)
    channel = args.channel
    if prompt in PROMPTS:
        channels = studio.channels_overview(home) if (home / "channels").exists() else []
        channel = channel or (channels[0]["name"] if channels else "")
        if "{channel}" in PROMPTS[prompt] and not channel:
            raise SystemExit("No channel yet. Run `try setup` first, or `sandbox --seed`.")
        script = {}
        if "{script}" in PROMPTS[prompt]:
            folder = studio.find_channel(home, channel)
            scripts = studio.Studio(folder, home).scripts()
            if not scripts:
                raise SystemExit("No scripts in that channel yet.")
            script = scripts[0]
        prompt = PROMPTS[prompt].format(channel=channel, script=script.get("id", ""), script_title=script.get("title", ""))
    env = {**os.environ, "VID_STUDIO_HOME": str(home)}
    if args.agent == "claude":
        command = ["claude", "-p", prompt, "--permission-mode", "acceptEdits",
                   "--allowedTools", "Bash(python3:*) WebSearch WebFetch Read Write Edit Glob Grep"]
    else:
        command = ["codex", "exec", "-C", str(root), "--skip-git-repo-check", "--sandbox", "workspace-write",
                   "-c", "sandbox_workspace_write.network_access=true", prompt]
    if not shutil.which(command[0]):
        raise SystemExit(f"`{command[0]}` is not on your PATH.")
    print(f"$ {args.agent}: {prompt}\n", flush=True)
    subprocess.run(command, cwd=root, env=env)
    print("\n--- studio after the run ---")
    print(run_studio(home, "status", *(["--channel", channel] if channel else []), check=False))
    serve(home, False)


def cmd_reset(args) -> None:
    home = Path(args.path).expanduser().resolve() / "studio"
    if not args.yes:
        raise SystemExit(f"This deletes all test data in {home}. Run again with --yes.")
    run_studio(home, "serve", "--stop", check=False)
    shutil.rmtree(home, ignore_errors=True)
    print(f"Wiped {home}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    sub = commands.add_parser("demo", help="Throwaway studio with sample data, opened in the browser")
    sub.add_argument("--no-open", action="store_true")
    sub.set_defaults(handler=cmd_demo)

    sub = commands.add_parser("sandbox", help="Create or refresh the test project")
    sub.add_argument("--path", default=str(SANDBOX))
    sub.add_argument("--seed", action="store_true", help="Fill the sandbox studio with sample data")
    sub.set_defaults(handler=cmd_sandbox)

    sub = commands.add_parser("try", help=f"Run an agent in the sandbox: {', '.join(PROMPTS)}, or any prompt")
    sub.add_argument("prompt", nargs="+")
    sub.add_argument("--agent", choices=["claude", "codex"], default="claude")
    sub.add_argument("--channel")
    sub.add_argument("--path", default=str(SANDBOX))
    sub.set_defaults(handler=cmd_try)

    sub = commands.add_parser("reset", help="Delete the sandbox's studio data")
    sub.add_argument("--path", default=str(SANDBOX))
    sub.add_argument("--yes", action="store_true")
    sub.set_defaults(handler=cmd_reset)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
