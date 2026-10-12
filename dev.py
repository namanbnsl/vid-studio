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
    "setup": ("Use the vid-studio skill to set up a project called \"Test Plumbing\": Indian plumbing and bathroom products "
              "for homeowners and dealers, in Hinglish, timezone Asia/Kolkata. Don't ask me anything: choose 4 topics and "
              "about 6 sources yourself, add the sources as suggestions, and open the studio."),
    "research": "Use the vid-studio skill to research now for the project \"{project}\".",
    "story": "Use the vid-studio skill to research the story \"{story_title}\" ({story}) in the project \"{project}\".",
    "draft": "Use the vid-studio skill to write the script \"{script_title}\" ({script}) in the project \"{project}\".",
    "status": "Use the vid-studio skill: what's new in the project \"{project}\"?",
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

SENSOR_SCRIPT = """## Hook
Jaquar के नए sensor नल ₹6,500 से शुरू होते हैं, और company कहती है कि इनसे आधा पानी बचता है. [1]
Visual: stat | ₹6,500 | Jaquar sensor tap | starting price
Source: Jaquar, October 2026

## How it saves
तरीका सीधा है. हाथ नीचे लाओ तो पानी चलता है, हटाओ तो बंद. Brush करते वक़्त जो पानी यूँ ही बहता रहता है, वही बचता है.
Visual: list | पानी कहाँ बचता है | Brush करते वक़्त | बर्तन धोते वक़्त | साबुन लगाते वक़्त

## The catch
लेकिन ये 50 percent वाला आँकड़ा Jaquar का अपना है. किसी independent lab ने अभी तक इसे test नहीं किया. [1]
Visual: compare | पानी की खपत | आम नल: 100 | Sensor नल: 50
Text: Company का दावा
Source: Jaquar press release

## Where it pays
तो लगाना है, तो kitchen में या उस bathroom में लगाओ जहाँ नल दिन भर चलता है. पैसा वहीं सबसे जल्दी वसूल होगा.
Visual: image | Kitchen sink with a sensor tap, water running

## End
घर की ऐसी ही काम की बातें, रोज़ Pipe Gyaan पर.
Visual: end | पानी बचाओ, पैसा भी | Follow @pipegyaan
"""


def seed(home: Path) -> None:
    """Two projects with topics, sources, a finished run, findings, stories, and scripts on three channels."""
    (home / "projects").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SKILL / "assets" / "README.md", home / "README.md")

    folder = studio.create_project(home, "Pipe Gyaan", "Plumbing, sanitaryware और bathroom की हर बात, आसान भाषा में।")
    pipe = studio.Studio(folder, home)
    studio.add_channel(home, {"name": "Pipe Gyaan", "platform": "YouTube Shorts", "language": "Hinglish",
                              "audience": "Indian homeowners, plumbers and dealers"})
    studio.add_channel(home, {"name": "Pipe Gyaan WhatsApp", "platform": "WhatsApp channel", "kind": "post", "language": "Hinglish"})
    studio.add_channel(home, {"name": "Explained in 90s", "platform": "YouTube Shorts", "language": "English"})
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
    story = pipe.create_story("Sensor taps: पैसा बचेगा या नहीं?", [sensor["id"]])
    pipe.update_story(story["id"], {
        "notes": ("# Research notes\n\n## What's new\n- Jaquar's touchless range starts at **₹6,500**. [1]\n"
                  "- The 50% water saving is the maker's claim; no independent test yet.\n\n"
                  "## Sources\n1. Jaquar, Sensor faucets, https://www.jaquar.com/news/sensor\n")})
    script = pipe.create_script(story["id"], "pipe-gyaan")
    pipe.update_script(script["id"], {"stage": "ready", "text": SENSOR_SCRIPT})
    pipe.save_angles(script["id"], [
        {"hook": "Jaquar के नए sensor नल ₹6,500 से शुरू होते हैं, और company कहती है कि इनसे आधा पानी बचता है.", "angle": "Price vs claimed savings", "why": "Number first, claim second: the gap is the open loop.", "chosen": True},
        {"hook": "आपका नल रोज़ कितना पानी बहा देता है? ये वाला कहता है, आधा कम.", "angle": "Your daily waste", "why": "Makes it about the viewer, but the answer isn't sourced yet."},
        {"hook": "Touchless नल hospital के लिए बने थे. अब घर आ रहे हैं.", "angle": "Hospital tech goes home", "why": "Story hook; weaker stakes for a homeowner."}])
    pipe.save_review(script["id"], {"scores": {"hook": 8, "clarity": 9, "retention": 7, "specificity": 8, "voice": 8, "natural": 7, "value": 8, "accuracy": 7},
                                    "summary": "Strong price-first hook; the 50% claim still needs clear attribution.",
                                    "notes": ["Retention dips in the middle beat; add a re-hook before the payback math.",
                                              "Say that the 50% figure is Jaquar's own claim."]})
    pipe.add_comment(script["id"], "Can we name a real test, or show the payback math?", "किसी independent lab ने अभी तक इसे test नहीं किया")
    post = pipe.create_script(story["id"], "pipe-gyaan-whatsapp")
    pipe.update_script(post["id"], {"text": "*Sensor taps: पैसा बचेगा?*\n\nJaquar के नए sensor faucets ₹6,500 से शुरू। [1]\n\nhttps://www.jaquar.com/news/sensor\n",
                                    "stage": "published", "published_url": "https://whatsapp.com/channel/example"})
    pipe.create_story("Water tank को साफ़ कैसे रखें", topic_ids=["water-tanks"])

    folder = studio.create_project(home, "Explained in 90s", "Indian tech and money news, explained in 90 seconds.")
    news = studio.Studio(folder, home)
    news.add_topic("UPI & payments", "Fees, NPCI rules, fraud, new features.")
    news.add_source("https://rbi.org.in", "Press releases")
    run, _, _ = news.start_run()
    news.add_findings(run["id"], [{"title": "How UPI Lite's payment and wallet caps differ",
                                   "summary": "An evergreen explainer: a PIN-free payment cap is different from the amount held in the Lite balance. Verify provider documentation before drafting.", "topics": ["UPI & payments"],
                                   "sources": [{"url": "https://support.google.com/pay/india/answer/13327133?hl=en-IN", "publisher": "Google Pay Help"}]}])
    news.mark_checked(run["id"], run["sources"], "demo fixture, not a live research run")
    news.finish_run(run["id"])
    upi = news.create_story("UPI Lite: PIN-free payments, explained", [news.findings()[0]["id"]])
    news.create_script(upi["id"], "explained-in-90s")


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
    if args.seed and not studio.project_dirs(home):
        seed(home)
    print(f"Sandbox: {root}\nStudio data: {home}\nThe skill is linked to {SKILL}, so edits apply immediately.\n")
    print(f"Try it:\n  cd {root} && claude          # then: Use vid-studio to set up my project\n"
          f"  python3 {Path(__file__).name} try setup      # or run it headlessly")


def cmd_try(args) -> None:
    root = Path(args.path).expanduser().resolve()
    home = root / "studio"
    if not (root / ".claude" / "skills" / "vid-studio").exists():
        raise SystemExit(f"No sandbox at {root}. Run: python3 {Path(__file__).name} sandbox")
    prompt = " ".join(args.prompt)
    project = args.project
    if prompt in PROMPTS:
        projects = studio.projects_overview(home) if (home / "projects").exists() else []
        project = project or (projects[0]["name"] if projects else "")
        if "{project}" in PROMPTS[prompt] and not project:
            raise SystemExit("No project yet. Run `try setup` first, or `sandbox --seed`.")
        picked = {}
        for kind in ("story", "script"):
            if "{" + kind + "}" in PROMPTS[prompt]:
                folder = studio.find_project(home, project)
                items = getattr(studio.Studio(folder, home), kind.replace("story", "storie") + "s")()
                if not items:
                    raise SystemExit(f"No {kind.replace('story', 'storie')}s in that project yet.")
                picked = {kind: items[0]["id"], kind + "_title": items[0]["title"]}
        prompt = PROMPTS[prompt].format(project=project, **{"story": "", "story_title": "", "script": "", "script_title": ""} | picked)
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
    print(run_studio(home, "status", *(["--project", project] if project else []), check=False))
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
    sub.add_argument("--project")
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
