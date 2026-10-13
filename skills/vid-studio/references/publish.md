# Publish

A video channel can be connected to the account it publishes to: a **YouTube** channel, an **Instagram** professional account (Reels), or a **TikTok** account. The studio then uploads the rendered MP4 straight from this computer with the platform's official API, and marks the script published with the link. Text-post channels (WhatsApp) are still shared by hand.

**Publishing is public and hard to undo.** Only publish when the user asks to publish *that* script in this conversation (or clicks Publish in the UI). Say the account, the visibility, and the title before you do it, and use `--yes` only once they've confirmed. Never publish as part of writing, revising, or rendering. Scheduled runs never publish.

`studio.py platforms` shows each platform and where each channel publishes.

## Connect a channel

Each platform needs something only the user can make. Walk them through it once; the UI's Channels → channel → **Publishing** tab shows the same steps.

- **YouTube.** The user creates their own OAuth client in Google Cloud: a project with the *YouTube Data API v3* enabled, an OAuth consent screen (add themselves as a test user), and credentials of type **Desktop app**. They paste the client ID and secret in the UI, or you run `studio.py platform-app --platform youtube --id CLIENT_ID --secret -` and they pipe in the secret. Then **Connect YouTube** in the UI, or `studio.py connect --channel C` (the studio must be running) prints a link to open; they sign in and approve, and the channel is connected. Allowing captions asks for broader access ("manage your videos"); without it the captions file is simply not uploaded. Uploads from an unverified Google project are private until Google audits it; that's expected for personal use.
- **Instagram.** The account must be a professional (Business or Creator) account. In a Meta app with *Instagram API with Instagram login*, the user adds the account as a tester and clicks **Generate token**. They paste it in the UI, or into `studio.py connect --channel C --platform instagram --token -`. The studio refreshes it before it expires (60 days).
- **TikTok.** The user creates a TikTok app with *Login Kit for Desktop* and the *Content Posting API*, registers the redirect URI the UI shows (`http://localhost:8765/oauth/callback`), and saves the client key and secret (`studio.py platform-app --platform tiktok`). Then **Connect TikTok**. Until TikTok audits the app, it can only post privately ("Only me"); **Draft** (the default) sends the video to the TikTok app's inbox, where they finish posting.

Tokens are kept in the studio's `.secrets.json` (readable only by the user). Never print, log, or repeat a token or secret. `studio.py disconnect --channel C` forgets the token and asks the platform to revoke it.

Channel defaults (`studio.py publishing --channel C --file -`): `privacy`, `category` (YouTube: 27 Education, 25 News & Politics, 28 Science & Technology), `made_for_kids`, `synthetic`, `hashtags`, `captions`, `thumbnail`.

## Write the post details

"Write the post details for the script …" means: write them, don't publish. Read the script and its story notes, then save with `studio.py publish-details --script S --file -`:

```json
{"title": "UPI Lite की limit अब ₹5,000: क्या बदला?",
 "description": "UPI Lite से अब बिना PIN एक बार में ₹1,000 तक दे सकते हैं, और wallet में ₹5,000 तक रख सकते हैं. किसके लिए काम का है, और कहाँ सावधान रहें.",
 "caption": "बिना PIN ₹1,000 तक. पर wallet की limit अलग है. आपको कौन सी चाहिए?",
 "hashtags": ["upi", "upilite", "money"], "tags": ["upi lite", "npci", "upi limit"]}
```

- **title** (YouTube, at most 100 characters): what the viewer gets, in the channel's language, without clickbait or all-caps. The hook's promise, not a label.
- **description** (YouTube): two or three plain lines on what the video covers and for whom.
- **caption** (Instagram, TikTok): the hook line, a line of context, and a question that invites a comment. Under 300 characters reads best.
- **hashtags**: 3–5 specific ones; **tags** (YouTube search): a few phrases people search for.
- Optional: `privacy`, `publish_at` (YouTube only: an ISO time; it uploads private and goes public then), `synthetic` (the platform's "altered or synthetic" label; a narrated explainer usually doesn't need it, but say so if the visuals show realistic people or events that didn't happen), `made_for_kids`, `category`, `captions`, `thumbnail`.

Don't add sources, photo credits, or the hashtags to the text yourself: when it posts, the studio appends the story's source links (YouTube), the photo credits the licences require, and the hashtags. Use the same language rules as the script.

## Publish

1. The video must be rendered and current (`studio.py render --script S`; the UI says "Video outdated" otherwise).
2. `studio.py publish --script S` shows what would be posted, where, and how; after the user confirms, run it again with `--yes`. It prints the link.
3. A YouTube upload that stops midway resumes where it stopped the next time. Instagram and TikTok process the video before it's live; the command waits.
4. The script moves to **Published** with its link. `studio.py stats --script S` fetches views, likes and comments later.

YouTube can schedule (`publish_at`); Instagram and TikTok can't through their APIs, so they publish now. A day's YouTube upload quota fits about six videos on a new Google project.
