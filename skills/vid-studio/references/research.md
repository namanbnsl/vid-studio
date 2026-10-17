# Research run

Goal: new findings in the feed. A finding is a real development since the last run, on one of the project's topics, that the audience would care about. Each finding is backed by pages you opened. You decide how to search and how deep to go.

Read the feed the way the audience would. A rate change, a launch or a circular matters because of what it does to someone: what they pay, what they're asked to do, what can go wrong for them. Look for that person in every finding, and say who it lands on. The best stories often start in the audience's own words: a question that keeps coming up, a complaint that's spreading, a confusion a new rule creates.

## Steps

1. Run `studio.py start-run` (add `--trigger scheduled` for scheduled runs). It prints the run ID, the time to look back to, and the approved sources this run must check.
2. Read the topics and their descriptions, plus `research_notes` in `studio.json`. Look at recent findings, including dismissed ones (dismissed means the user didn't want it), so you don't add them again.
3. **Check every approved source.** This is required. `studio.py scan` lists new items from sources that have feeds; search the rest directly (for example with `site:` queries). After checking each one, run `studio.py checked --run RUN --source ID --note "what you found"`. If a site can't be reached, still mark it, and say so in the note. The run cannot finish until every source is marked.
4. **Search the wider web** for every topic as well. Your sources are the minimum, not the limit.
   - **Listen to the audience, too.** Look at where they talk: public forums, comment threads under coverage, app-store reviews, consumer complaint sites, help-centre pages. A sudden wave of the same question or complaint is a finding in its own right if a page you opened documents it (a published article about it, an official advisory, a help page that was just added). Forum posts are leads, not sources: follow them to something you can cite.
5. Save findings with `studio.py add-findings --run RUN FILE`:

```json
[{"title": "Short headline, about 10 words",
  "summary": "One plain sentence: what happened, and who it lands on.",
  "topics": ["Topic name or ID"],
  "sources": [{"url": "https://…", "title": "Article title", "publisher": "Reuters", "published": "2026-10-08"}]}]
```

   - Keep findings short: a headline (110 characters at most) and a one-sentence summary (240 at most). The helper rejects longer ones. Detail belongs in a script's fact sheet.
   - **Write them like a person telling a colleague,** not like a press release. Name who's affected and how: "Jaquar's sensor taps now start at ₹6,500; the 50% water saving is the company's own figure" beats "Jaquar unveils innovative touchless faucet range". No adjectives the source didn't earn (innovative, major, game-changing).
   - Write titles and summaries in English, whatever language the channels use. Only scripts use it.
   - Every finding needs at least one topic and at least one page you opened. Prefer original pages, such as the regulator, the company, or the dataset.
   - Coverage of the same development from several outlets is **one** finding with several sources. If a URL is already in the feed, the helper merges into that finding.
   - The UI labels each finding "Your source" or "Found on the web" automatically, from the URLs.
   - Skip anything that isn't new, isn't relevant, or can't be sourced.
6. **Suggest sources.** If a site outside the approved list proved valuable (an original source, or one that keeps breaking the stories), suggest it with `studio.py suggest-source --run RUN --url URL --reason "why it deserves checking every run"`. The user approves or dismisses it in the Sources tab. Don't re-suggest dismissed sites; the helper refuses anyway.
7. Run `studio.py finish-run --run RUN`. If the run broke, use `--failed "reason"` instead, so the next run looks back from the last good one.
8. Reply with how many findings you added, the two or three most notable, any sources you suggested, and the studio link (`studio.py serve --background`).

If nothing new turned up, finish the run anyway and say so. That's a valid result.
