# Vid Studio

A skill for running research for explainer videos with any AI agent that supports [skills](https://skills.sh/), such as Claude, ChatGPT, or Codex. All data stays in a local folder, and you work in a small web UI.

```sh
npx skills add namanbnsl/vid-studio
```

## How it works

The studio has three global tabs: **Research**, **Production**, and **Channels**. They stay available wherever you are in the app.

**Research** happens in **projects** (each one a subject area, such as plumbing products or Indian tech news), and you switch between them in the UI. Each project has:

- **Topics:** what the project makes videos about. Each one is a name plus a description of what matters.
- **Sources:** websites every research run must check. Research also suggests new ones for you to approve.
- **Findings:** short items on new developments, each linked to its topics and to the pages it came from. Dismiss what you don't need.
- **Stories:** an angle for a video, built from findings, topics, or both, with research notes.

**Production** shows scripts from every research project on one board, with optional project and channel filters. A story becomes one script per channel you send it to. Scripts move through stages (script, ready, published), and you can comment on any passage for your agent to address. Each script links back to its source story and to its channel.

**Channels** manages publishing destinations (each YouTube channel, Instagram account, TikTok account, or WhatsApp channel), shared across the studio, and connects video channels to their real accounts. They set each script's language, format, look, and voice. One research story can become an English Short, a Hinglish Reel, and a Hindi WhatsApp post. You can set up channels before adding a research project.

The information flow is **Research story → Production scripts → Channels**. Research stays reusable; each script adapts that evidence for its destination. Projects organize Research and appear as source labels or optional filters in Production.

Each channel has a **Voice** (length, pace, persona, tone, hook styles, rules, and scripts you love) and, for video channels, a **Look** (one of twelve styles to start from, then colors, fonts with Hindi support, motion, captions with a highlight or underline that follows the voice, photo treatment and placement, source tags, a progress line with a folio, background, logo). You set both up when you add a channel, with a live preview of animated sample scenes in that look.

**Human, start to finish.** Research looks for the people a story lands on, the everyday moment they meet it, and the questions they actually ask. Story notes record them; scripts are about someone (a real case, the viewer, or an openly hypothetical relative, never an invented "Rahul from Pune"), carry a point of view the evidence earns, and are scored on whether they feel human as well as whether they sound it. The linter catches invented characters, fake anecdotes, reframes, fragment chains and flat rhythm.

Video scripts are written as beats: what's said, plus a `Visual:` line naming a scene (a stat, bar chart, comparison, list, quote, timeline, photo, punchline, or the message or call the story turns on). A beat can also have a photo behind it (`Image:`), a small on-screen source tag (`Source:`), and a fixed length (`Duration:`). The script editor plays them as an animated preview in the channel's look as you type, shows the timing against the target, the hooks your agent considered (swap one in with a click), and its self-review scores, including whether it tells a human story, whether it sounds human, and whether it's worth the viewer's minute.

**Images.** Photos run edge to edge across the top of the frame, like the picture on a magazine page, with the scene set below (beside it in wide formats), or faint behind charts. Your agent picks photos for the beats about real things and people: openly licensed photos from Wikimedia Commons and Openverse (no API key; it looks at previews before choosing), or images it generates with its own image tool, if it has one. Generated images are never used for real people, products, logos, or documents. Every photo is saved with the script and credited on screen. You can also add your own photo to any beat from the script page.

**Voiceover.** Give a video channel a narrator on its **Narration** tab: a voice on your computer (the system voice, or free offline [Piper](https://github.com/OHF-Voice/piper1-gpl) voices), or ElevenLabs, Sarvam AI, OpenAI or Google Cloud with your own API key. Hear samples, set the speed, the pause between beats, and how words are pronounced. Each beat is voiced on its own and reused until its line changes; beats then last as long as the voice takes, captions follow it (word by word with ElevenLabs), and a `Say:` line lets the voice read "twelve thousand rupees" while the screen shows ₹12,000. The MP4 gets the voiceover, mixed to a loudness phones expect, plus an `.srt` captions file.

**Publish.** Connect a video channel to its YouTube channel, Instagram professional account, or TikTok account on its **Publishing** tab. On a script's **Post** tab, check the title, description or caption, hashtags, visibility and (on YouTube) a release time, then click **Publish**: the MP4 uploads from your computer with each platform's official API, with the poster as the thumbnail, the voiceover's captions, and the sources and photo credits appended. The script moves to Published with its link, and its views show on the board. You bring your own Google Cloud or TikTok app (or an Instagram token), so nobody else holds your access; tokens stay in the studio's `.secrets.json`.

**Download.** Click **Render MP4** on a script, then **Download MP4**: the video renders on your computer (1080p, 30 fps) with Chrome and ffmpeg, which you need installed. Your agent can do the same with `studio.py render --script ID --out ~/Desktop`. `studio.py export` writes the same video as a [HyperFrames](https://github.com/heygen-com/hyperframes) project instead.

The steps that need an AI each have a button that copies a prompt. Paste it into Claude or ChatGPT, and the results show up in the UI:

- **Research now:** your agent researches every topic and adds findings.
- **Research story:** your agent researches a story's findings and topics in depth and writes its notes.
- **Send to production**, then **Write draft:** your agent writes each channel's script from the story's notes, following a craft guide: several hooks, a plain-spoken first pass, a beat outline, photos and sources, timing, a pass to remove anything that sounds machine-made, and an honest self-review against a rubric. With open comments, the button becomes **Revise**, and your agent works through them in order.
- **Ask your agent** (on a channel's Look and Voice): describe a change in words, and your agent makes it.

To research on a schedule, click the schedule link under **Research now**, pick the days and times, and paste the copied prompt into your agent. It creates the scheduled task.

## Start

> Use vid-studio to set up my project.

Your agent creates the studio (`~/vid-studio` by default, one folder per project in `projects/`), proposes topics and sources, and opens the studio at `http://localhost:8765`. Later, "Use vid-studio, open the studio" brings it back.

## Files

```
skills/vid-studio/
  SKILL.md            entry point
  references/         setup, research, story, write, script craft, scenes, images, look, narration, publish, schedule
  scripts/studio.py   helper and local web server (Python 3 standard library)
  scripts/narration.py text-to-speech providers: system, Piper, ElevenLabs, Sarvam, OpenAI, Google (standard library)
  scripts/publish.py  YouTube, Instagram Reels and TikTok publishing with their official APIs (standard library)
  scripts/render.py   MP4 renderer: drives a local Chrome and ffmpeg (standard library)
  assets/             workspace templates, the UI, the scene engine (assets/scenes), and example scripts
```

The workspace is plain JSON and Markdown, so it is easy to back up, read, or edit by hand.

## Develop

```sh
python3 dev.py demo              # throwaway studio full of sample data, opened in your browser
python3 dev.py sandbox --seed    # test project at ../vid-studio-sandbox, with the skill linked (not copied)
python3 dev.py try setup         # run Claude Code headlessly in the sandbox (setup, research, story, draft, status, or any prompt)
python3 dev.py try research --agent codex
python3 dev.py reset --yes       # wipe the sandbox's studio data
python3 -m unittest discover tests
node --test tests/test_ui.js tests/test_engine.js
```

The sandbox links the skill into `.claude/skills` and `.agents/skills`, so edits to this repo apply on the next prompt with no reinstall. Its studio data lives in the sandbox, so your real `~/vid-studio` is never touched. For interactive testing: `cd ../vid-studio-sandbox && claude`.
