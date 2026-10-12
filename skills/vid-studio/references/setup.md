# Setup

Goal: a named project with a few good topics and sources, and the studio open. Keep it quick: the user can refine everything later in the UI. The same steps add a second or third project.

1. Run `studio.py init`. It never overwrites existing files. If the user wants the studio somewhere other than `~/vid-studio`, suggest they set `VID_STUDIO_HOME`, or include the path in their prompts.
2. In one short message, ask for:
   - the project name and what it covers
   - the audience
   - the timezone
   - the subjects they want to follow
   - where they publish: each channel (YouTube, Instagram, WhatsApp, …) and its language: English, Hindi, or Hinglish (Hindi in Devanagari mixed with English terms). Research stays in English.
   - who's talking on each channel, in a line: the person the viewer should hear (for example "a plumber with 20 years on site, blunt and practical" or "an elder sister who works in a bank"). Save it as the channel's voice `persona`; it shapes every script far more than any rule.

   Create the project with `studio.py new-project --name N --description D`, then fill in `audience` and `timezone` in its `projects/<id>/studio.json`. Use `--project N` on every command after this. Add each channel that doesn't exist yet (`studio.py channels`; they're shared by every project) with `studio.py add-channel --name N --platform P --kind video|post --language L`. The default format for each kind is fine unless they have a house style; if they share example scripts or posts, pass that style with `--format`.
3. **Propose topics.** Suggest 3–8 topics, each with a description of what matters and what to ignore, written from the audience's side: what they're deciding, what they worry about, what they keep asking. Topics are subjects, not single stories. Add the ones they accept with `studio.py add-topic --name N --description D`.
4. **Suggest sources.** Find about 5–15 sites worth checking on every run: official bodies, data publishers, and outlets with original reporting. Open each one first to confirm it's live and relevant. Add each with `studio.py suggest-source --url U --reason "why"`. The user approves or dismisses them in the Sources tab. If the user approves in chat instead, use `studio.py add-source --url U --note N`, which adds the source as approved.
5. Run `studio.py serve --background` and share the link. Offer a first research run and a research schedule ([schedule.md](schedule.md)).
