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

Find sources that will keep surfacing relevant, trustworthy stories for the user's interests. Go primary where you can: official bodies, data publishers, original reporting. Mix them as you see fit with feeds, Google News queries, Alerts, and Trends.

- Only propose sources you have actually opened and confirmed are live.
- After adding a Google News query, scan it once (`studio.py scan --source ID --limit 10`) and check the results are on-topic. Bare acronyms often match unrelated outlets.
- Show the candidates with a reason for each. Add the ones the user approves. If the user said not to gate sources, add them all and report the list.

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

Propose topics this audience will care about, with something real to explain and enough evidence to show. Draw on the inbox, Trends, the user's interests, gaps in past projects, or anything else you judge useful. Skip any that duplicate active topics or past projects (check `topics.json` and `projects/`).

For each topic, give a mode (`once` or `daily`), an angle, and why now. Add each one with `add-topic --title T --mode once|daily --angle A --why W [--query Q]... [--source ID]... --status proposed`. Use `--status active` if `review.topics` is false or the user already approved it.

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
