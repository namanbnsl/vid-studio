# Setup

Goal: a named channel with a few good topics and sources, and the studio open. Keep it quick: the user can refine everything later in the UI.

1. Run `studio.py init`. It never overwrites existing files. If the user wants the workspace somewhere other than `~/vid-studio`, suggest they set `VID_STUDIO_HOME`, or include the path in their prompts.
2. In one short message, ask for:
   - the channel name and what it covers
   - the audience
   - the language
   - the timezone
   - the subjects they want to follow

   Save the answers to `studio.json`: `name`, `description`, `audience`, `language`, and `timezone`. The default `script_format` and `post_format` are fine unless they have a house style; if they share example scripts or posts, write that style into those fields.
3. **Propose topics.** Suggest 3–8 topics, each with a description of what matters and what to ignore. Topics are subjects, not single stories. Add the ones they accept with `studio.py add-topic --name N --description D`.
4. **Suggest sources.** Find about 5–15 sites worth checking on every run: official bodies, data publishers, and outlets with original reporting. Open each one first to confirm it's live and relevant. Add each with `studio.py suggest-source --url U --reason "why"`. The user approves or dismisses them in the Sources tab. If the user approves in chat instead, use `studio.py add-source --url U --note N`, which adds the source as approved.
5. Run `studio.py serve --background` and share the link. Offer a first research run and a daily schedule ([schedule.md](schedule.md)).
