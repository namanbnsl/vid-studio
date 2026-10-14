# Research a story

The prompt names a story, like `"Title" (story-id)`. Its files are in `stories/<id>/`:
- `story.json`: the title, linked `findings` (IDs in `findings.json`), and linked `topics` (IDs in `topics.json`)
- `notes.md`: the research notes you write

A story is research, not a script. Every script made from it, on any channel, reads these notes, so research once and well. Notes are always in English.

A story can be one of three kinds:
- **News:** findings only. The story is the development; research what happened, why, and what it means.
- **Explainer:** topics only. Research the subject from scratch: background, how it works, the key numbers, and current state. Use reference sources such as official explainers, company or regulator pages, papers, data, and good encyclopedic overviews.
- **Both:** a news hook leading into an explainer. Use the findings for the hook and the topic for the depth.

## Research until you could explain it to anyone

The script can only be as clear as your understanding. If the notes say *what* happened but not *why*, or use a term without saying what it means, the script will too, and the viewer will be lost. So research like someone who has to explain this tomorrow to a friend who knows nothing about the field and will ask "wait, what's that?" after every sentence.

- **Go past the first article.** News coverage repeats itself and skips the basics. For every story, open the primary source (the regulator's circular, the company's announcement, the paper, the dataset, the court order), at least two independent reports, and at least one explainer or reference page for the background. Aim for 8 or more pages actually read for a news story, more for an explainer. Stop when new pages stop telling you anything new, not when you have enough to fill the template.
- **Find out what came before.** What was the situation before this? What problem was it meant to fix? Who pushed for it? A development only makes sense next to what it replaced.
- **Understand the mechanism step by step.** How does the thing actually work, in order, with nothing skipped? If you can't write the steps, you don't understand it yet, so keep reading. Official explainers and FAQs are written for the public, which makes them good for this.
- **Write down every name and term the story uses, with a plain explanation.** Who is this company, what does this regulator do, what does this word mean. One line each, in everyday words, the way you'd say it out loud ("RBI: India's central bank, which makes the rules banks follow"). Source the explanation like any other fact.
- **Find a comparison the viewer already knows.** Something from daily life that works the same way, so the mechanism clicks: a UPI PIN is the signature on a cheque. Note where the comparison breaks.
- **Give numbers a size.** For every number worth showing, find what it's against: last year's figure, the average, the price of something familiar, the share of the total. A number with no comparison isn't worth showing.
- **Check every fact a script will rely on in two places,** especially numbers, dates and names. When sources disagree, note both and which one is the original.
- **Look for what most coverage misses.** The fine print in the primary document, the caveat in paragraph twelve, the person nobody quoted. That's usually where the video's value is.

## Research the people, not just the facts

A video that only recites facts sounds like a model wrote it, however accurate it is. What makes a viewer stay is a person they recognise: themselves at a shop counter, a parent on the phone with a "bank officer", the engineer who decided how the thing works. The writer can't invent any of that later; it has to be in the notes. So, alongside the facts, look for:

- **Who it happens to.** The people the story lands on, and in what situation. Find real, on-record cases: someone named in reporting, a regulator's order or court judgment that describes a case, an official complaint statistic. A typical viewer's situation is fine too, but write it as typical ("a salaried person paying rent in a metro"), never as a made-up person with a name.
- **Who decided it, and why.** The company, regulator, or person behind the change, and the reason they gave in their own words. A real decision-maker with a motive is a story; "new rules came in" is not.
- **The moment.** The concrete, everyday scene where the audience meets this: the refund call, salary day, the bill, the counter, the screen with the button. Note the exact words on the screen or the exact phrase people hear, from a source if you can.
- **What people believe and ask.** The misconception the audience holds, and the questions they actually type or post. Public forums, comment sections, help pages and "people also ask" boxes show the real words. Note a few, with where you saw them; they become hooks and re-hooks.
- **The tension.** The claim versus the evidence, the cost versus the benefit, the thing that's true but surprising, the people who disagree. If there's no tension, say so: it might be a post, not a video.
- **Lived detail.** The physical, specific things that make it real: the colour of the button, what the form asks for, how long the queue is, what it costs next to something people buy. Only what a source shows.
- **Real voices.** Exact quotes from people involved, word for word, with who said it and where. A regulator's line, a founder's claim, a user's complaint in a published article. Never paraphrase inside quote marks.
- **Pictures.** The real things the video could show: the product, the place, the document, the screen, the person in their role. Note what to look for ([images.md](images.md)) so the writer doesn't settle for "money concept".

Never invent any of it. A person, a quote, a scene or a forum post you didn't actually find doesn't go in the notes, however typical it sounds.

## Steps

1. Read the linked findings and topics, and `audience` and `research_notes` in `studio.json`. If nothing is linked, work from the title.
2. **Research in depth**, as the two sections above describe. Open the findings' sources, then go further: primary documents, data, background and history, how it works, opposing views, and the human material. Check the facts a script will rely on in two places, especially numbers and dates. Before you write, test yourself: could you explain the story, start to finish, to someone who has never heard of any of it, and answer their first three "but why?" questions? If not, keep reading.
3. **Write `notes.md`** as markdown, in this shape (skip a section only if you looked and there was nothing; say so in a line):

   ```markdown
   ## Angle
   One or two sentences: why this matters to the audience now, and the single thing they'll know after watching.

   ## What the viewer needs first
   The background someone who has never heard of this needs before anything else makes sense, in plain words.
   - What happened, in one sentence a 15-year-old would get [n].
   - What it was like before, and the problem this was meant to fix [n].
   - Every name and term the story uses, one line each: "NPCI: the body that runs UPI, the system behind every payment app" [n].
   - An everyday comparison for the mechanism, and where it breaks.

   ## The people
   - Who it happens to, in what situation (real cases with [n], or the typical viewer, labelled as typical).
   - Who decided it, and the reason they gave [n].
   - Who disagrees, and why [n].

   ## The moment
   The everyday scene where the viewer meets this, with the exact words on screen or on the call [n].

   ## What people believe, and what they ask
   - The misconception, and what's actually true [n].
   - "Real question, in their words" (where it was asked).

   ## What happened / how it works
   The facts, organised however suits the story, with [n] on every line. Write the mechanism as numbered steps in order, with nothing skipped.

   ## Numbers worth showing
   Each with something to compare it to.
   - ₹6,500: starting price of the range, against about ₹1,500 for a basic tap [1][4]
   - 50%: water saving, the maker's own claim, untested [1]

   ## Tension and caveats
   The claim versus the evidence, what's disputed, what isn't known yet.

   ## What the viewer can do
   The decision rule, the check, the number to call, the date that matters [n].

   ## Quotes
   > "Exact words." (Who, where, date) [n]

   ## Pictures to find
   - The real things worth showing, as concrete search terms.

   ## Sources
   [1] Publisher, title, date, URL
   ```

4. **Read the notes cold,** as a writer who knows nothing else. Every name and term used anywhere in the notes should be explained under "What the viewer needs first", and every number should have a comparison. Fill the gaps before you finish.
5. **Respect the user's edits.** If `notes.md` already has text, add to it and correct it; don't throw it away unless the prompt asks for a fresh start.
6. Reply with a two-line summary (the angle, and the person or moment the story turns on) and the studio link. Mention that the user can send the story to production from the story page.
