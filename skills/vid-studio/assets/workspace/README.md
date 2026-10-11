# Vid Studio workspace

Managed by the `vid-studio` skill. Ask your agent: "Use vid-studio" and it picks up from here.

- `studio.json`: who you are, your audience, research rules, and the standard post/script format.
- `sources.json`: websites, feeds, Google News searches, Google Alerts, and Trends regions being monitored.
- `topics.json`: topics. `once` means one explainer. `daily` means check every day and make a video only when there is real news.
- `inbox/`: new items from each scan, one file per day.
- `projects/<date>-<topic>/`: one folder per video. Contains plan, sources, local evidence, claims, brief, WhatsApp post, and script.
- `digests/`: what each scheduled run did and what is waiting for you.

Edit any file by hand. The agent rereads it every time.
