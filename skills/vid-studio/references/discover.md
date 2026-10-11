# Sources, topics, scanning, triage

## Sources

A source is something checked on every scan. There are four kinds:

| Kind | Add with | Notes |
|---|---|---|
| Website or blog with RSS | `add-source --name N --url URL` | Feed auto-discovered. Falls back to a `page` you check manually. |
| Google News search | `add-source --news-query "QUERY"` | No account needed. Uses `studio.json` locale. Best general-purpose monitor. |
| Google Alerts | `add-source --kind alert --name N --feed RSS_URL` | The user creates the alert (see below) and pastes its RSS URL. |
| Google Trends | `add-source --trends-geo IN` | Daily trending searches for a country. Good for topic ideas, noisy as news. |

Add `--why "..."` to every source so later runs know what it is for.

### Finding sources

For each interest in `studio.json`:

1. **Primary sources.** These are regulators, ministries, statistics offices, central banks, standards bodies, company newsrooms and investor-relations pages, journals, and preprint servers. They are what you will cite most.
2. **Quality secondary sources.** Specialist outlets, reputable newspapers' section feeds, analyst newsletters, and research blogs. Prefer sources with original reporting over aggregators.
3. **One or two Google News queries per interest.** Use specific phrases and the names of key entities. Use operators where useful, such as `"RBI" digital lending` or `site:gov.in`.
4. **Google Alerts** for narrow terms Google News misses, like company names or bill numbers. Draft the exact queries for the user.
5. **One Trends feed** for the user's country, if they make timely content.

After adding a Google News query, run `studio.py scan --source ID --limit 10` and read the results. A bare acronym can match unrelated outlets: "UPI" also matches stories from upi.com. If the results are noisy, make the query more specific and re-add it.

Use web search to find candidates. Open each one to confirm it is live, relevant, and updated recently. A model's suggestion is only a lead until you have opened it.

Present 10-20 candidates in one table with columns name, kind, why, and feed found (yes/no). The user can approve all of them, remove some, or add their own. Then run `add-source` for each approved row. If the user said not to gate sources, add them and just report the list.

### Google Alerts setup (user does this)

Tell the user:

1. Go to google.com/alerts and enter the query.
2. Click **Show options** and set **Deliver to → RSS feed**. This needs a signed-in Google account.
3. Create the alert, click the RSS icon, and paste the feed URL here.

Never claim to have created an alert yourself.

### Managing sources

To pause a source, edit `sources.json` and set `"enabled": false`. To remove one, delete its record. Do not reuse IDs.

## Topics

A topic is something to make a video about.

- `once`: an explainer done once. Examples are evergreen concepts, a single event, or a "how X works".
- `daily`: an ongoing story checked every day. A video is made only when something meaningful changed. Examples are a policy rollout, a market, an ongoing case or conflict, or a product race.

Choose the mode from context and say why. If the user specifies a mode, use it.

### Finding topics

Pull candidates from:
- The inbox, as recurring stories across sources.
- Trends feeds, cross-checked against the user's interests.
- The interests themselves. Brainstorm "what does my audience misunderstand about X?" and "what changed in X this month?", then confirm each idea with a quick search.
- Gaps in existing projects, such as follow-ups and open questions in earlier briefs.

Score each candidate on four questions:
1. **Fit:** does this audience care?
2. **Explainability:** is there a mechanism or story to explain, not just a headline?
3. **Evidence:** are there sources and data to show?
4. **Timing:** why now?

Drop weak candidates. Also skip any that duplicate active topics or past projects (check `topics.json` and `projects/`).

Propose 5-10 topics in a table with columns title, mode, angle, why now, and the best sources. Add each one with `add-topic --title T --mode once|daily --angle A --why W --query Q... --source ID... --status proposed`. Use `--status active` if `review.topics` is false or the user already approved it.

When the user approves topics, set their `status` to `active` in `topics.json`. Other statuses are `paused`, `used` (a once topic already researched), and `archived`.

## Scan

1. Run `studio.py scan`. It fetches every feed, skips items seen before (including the same headline from different feeds), and appends new items to `inbox/<date>.md`.
2. The command lists pages without feeds. Open each one, note anything new since its last check, then run `studio.py checked ID...`.
3. Report failing feeds. If a feed keeps failing, find its new URL or disable it.

## Triage

Read new inbox items (today's file, plus earlier files since `last_triage` in `state.json`). Group items about the same story. For each story, take one of these actions:

- **It is about an active daily topic.** Run `studio.py lead --topic ID --url URL --title T --note "why it matters"`. The topic's next run starts from these leads.
- **It is a promising new topic.** Add it as a proposed topic, as described above.
- **Otherwise,** ignore it. Do not record anything.

Then run `studio.py triaged`. In interactive sessions, show the user a short list of the 3-5 most interesting stories.
