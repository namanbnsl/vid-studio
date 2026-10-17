# Get ideas

"Get video ideas" means: fill the project's Ideas list with evergreen videos the audience is already looking for. Ideas are not news and need no research run. Each is one question a video can answer, backed by a signal that real people ask or search for it.

## Steps

1. Read the topics and their descriptions, `audience` and `research_notes` in `studio.json`, and the current ideas in `ideas.json`, dismissed ones included (dismissed means the user didn't want it; don't add it again in other words).
2. **Collect the signals.** Run `studio.py idea-signals` (add `--query "…"` for a narrower subject, `--geo IN` to choose the country). It prints:
   - **Google autocomplete:** what people type after "how", "why", "what", "is", "can", "should" and "which" for each topic. These are real search phrasings.
   - **Google Trends:** searches rising today in the country. Most won't be about the project; use only the ones that are.
   - **Wikipedia pageviews:** the articles people read about each topic, with daily views this week and how that compares with the weeks before (×2.0 means double). A subject with steady high readership is a good explainer; a spike says people are trying to understand something right now.
3. **People also ask.** Search the web for each topic's main questions. If your search tool shows Google's "People also ask" box, note the questions it lists. Only record a `people-also-ask` signal for questions you actually saw there.
4. **Your own ideas.** Think about what this audience would want explained and what they get wrong about these topics. These are welcome, as long as you say they're your suggestion (`agent`).
5. **Pick 5–12 ideas worth a video.** For each:
   - A **title** (110 characters at most), in English, phrased the way the audience would ask it: "Why does my UPI payment fail but the money leaves my account?"
   - A **pitch** (280 at most): the one thing the video answers and why this audience cares. One question per idea; two questions are two ideas.
   - The **signal**: which kind (`people-also-ask`, `autocomplete`, `trends`, `wikipedia`, `agent`), the detail you saw ("autocomplete: 'why upi limit is 5000'", "Wikipedia: Unified Payments Interface, 2,100/day, ×1.8"), and its URL where there is one.
   - **Topics** it belongs to, by name or ID.
   Skip anything that is really news (that's a finding, from a research run), anything already in the list, and anything the project's topics don't cover.
6. Save them with `studio.py add-ideas -`:

```json
[{"title": "Why is there a ₹5,000 limit on some UPI payments?",
  "pitch": "People keep hitting a limit they didn't know existed. Which limits are NPCI's, which are the bank's, and how to see yours.",
  "topics": ["UPI & payments"],
  "signal": {"kind": "autocomplete", "detail": "\"why upi limit is 5000\" suggested for \"why upi\""}}]
```

7. Reply with how many ideas you added, the two or three strongest with their signal, and the studio link. The user sends the ones they want to production from the Ideas tab.

Never invent a signal: no search volume, pageview number, or "people are asking" you didn't see in the output or on a page. An idea is only a starting point: the script is still written from a fact sheet of sources you open ([facts.md](facts.md)).
