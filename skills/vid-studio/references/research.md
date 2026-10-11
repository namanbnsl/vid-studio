# Research run

Goal: new findings in the feed. A finding is a real development since the last run, on one of the channel's topics, that the audience would care about. Each finding is backed by pages you opened. You decide how to search and how deep to go.

## Steps

1. Run `studio.py start-run` (add `--trigger scheduled` for scheduled runs). It prints the run ID, the time to look back to, and the approved sources this run must check.
2. Read the topics and their descriptions, plus `research_notes` in `studio.json`. Look at recent findings, including dismissed ones (dismissed means the user didn't want it), so you don't add them again.
3. **Check every approved source.** This is required. `studio.py scan` lists new items from sources that have feeds; search the rest directly (for example with `site:` queries). After checking each one, run `studio.py checked --run RUN --source ID --note "what you found"`. If a site can't be reached, still mark it, and say so in the note. The run cannot finish until every source is marked.
4. **Search the wider web** for every topic as well. Your sources are the minimum, not the limit.
5. Save findings with `studio.py add-findings --run RUN FILE`:

```json
[{"title": "Short headline of the development",
  "summary": "2–3 plain sentences: what happened, and why it matters to this audience.",
  "topics": ["Topic name or ID"],
  "sources": [{"url": "https://…", "title": "Article title", "publisher": "Reuters", "published": "2026-10-08"}]}]
```

   - Every finding needs at least one topic and at least one page you opened. Prefer original pages, such as the regulator, the company, or the dataset.
   - Coverage of the same development from several outlets is **one** finding with several sources. If a URL is already in the feed, the helper merges into that finding.
   - The UI labels each finding "Your source" or "Found on the web" automatically, from the URLs.
   - Skip anything that isn't new, isn't relevant, or can't be sourced.
6. **Suggest sources.** If a site outside the approved list proved valuable (an original source, or one that keeps breaking the stories), suggest it with `studio.py suggest-source --run RUN --url URL --reason "why it deserves checking every run"`. The user approves or dismisses it in the Sources tab. Don't re-suggest dismissed sites; the helper refuses anyway.
7. Run `studio.py finish-run --run RUN`. If the run broke, use `--failed "reason"` instead, so the next run looks back from the last good one.
8. Reply with how many findings you added, the two or three most notable, any sources you suggested, and the studio link (`studio.py serve --background`).

If nothing new turned up, finish the run anyway and say so. That's a valid result.
