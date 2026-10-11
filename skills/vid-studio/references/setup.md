# Setup

Goal: a filled `studio.json`, a first set of sources, and a first set of topics. Aim for about 10 minutes of the user's time.

## 1. Create the workspace

Ask where the workspace should live only if the user cares; default to `~/vid-studio`. Then run `studio.py init`. Init never overwrites existing files, so it is safe to rerun.

If the user picks a non-default path, tell them to set `VID_STUDIO_HOME` in their shell profile, or pass `--workspace` every time. Scheduled runs need one or the other.

## 2. Interview

Ask in two or three short rounds, not one long form. Offer a sensible default for each question so the user can just say "yes".

Round 1, who and what:
- Their name and the channel or brand name.
- Audience: who watches, and what they already know.
- Language for scripts and posts. Country and region, which set `locale` for Google News and Trends.
- Timezone.
- Interests: 3-8 subject areas, as specific as possible. "Indian fintech regulation" is better than "finance".
- Topics or sources to avoid.

Round 2, format (show the default `format` from `studio.json` and ask what to change):
- Video length and aspect ratio.
- Tone, and title style.
- The beat structure. The default is Hook → Context → How it works → Evidence → So what → Takeaway.
- WhatsApp post style: length, emoji use, and structure.
- One or two example scripts, posts, or creators they like. Store paths or URLs in `format.examples`, and describe what to copy from each.

Round 3, research and automation:
- Trusted sources and blocked sources.
- Depth: `quick` (5-8 sources), `standard` (10-15), or `deep` (20+).
- Which review gates they want. The default is to approve new topics and the final script, and nothing else.
- Whether to schedule a daily run.

## 3. Save

Write the answers into `studio.json`. Keep any fields the user already customised. Set `setup_complete: true` once owner, audience, language, timezone, and interests are filled.

Show a five-line summary of the profile and the format. Apply corrections.

## 4. Continue without being asked

Go straight on to [discover.md](discover.md): propose sources, then topics. Then offer the daily schedule from [schedule.md](schedule.md).

## Changing preferences later

Edit `studio.json` directly when the user asks for a change. Projects that already exist keep their drafts. New work uses the new settings. If they want an open project updated, redo only its affected files.
