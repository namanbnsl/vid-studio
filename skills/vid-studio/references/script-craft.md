# Script craft

The bar: someone who never planned to watch stays to the end, learns one thing they repeat to a friend, and every claim survives a fact-check. It sounds like a person who knows the subject talking to one other person, not like a model, and even a viewer who suspects otherwise feels the minute was worth it. Generic is the failure mode. **If a line could appear in a video about a different topic, cut it.** And if the viewer can't say who the video was about, it's a lecture, not a story (§3).

The finished examples in `assets/examples/` show that bar: `english-60s.md`, `hinglish-60s.md`, `hindi-45s.md`. Read the one closest to the channel's language before your first draft.

## 1. The process

Do these in order, for every script. Don't skip steps because the topic seems simple; simple topics are where generic scripts come from.

1. **Find the angle.** Write down why this matters to *this* channel's audience *now*, and the single takeaway in 15 words or fewer (§2).
2. **Find the person and the moment.** From the notes' "The people" and "The moment", choose who this video is about and the scene where the viewer meets it, and decide what you, as the persona, think about it (§3).
3. **Write 3–5 hooks.** Use different styles from the channel's `hook_styles` and give each one a different angle, not the same angle reworded (§4).
4. **Pick the strongest and save them all.** Say why it wins (the most specific, the most surprising, the best fit for this audience). Save it with `studio.py angles --script ID --file -`:
   ```json
   {"angles": [
     {"hook": "UPI PIN डालने से पैसे आते नहीं. सिर्फ़ जाते हैं.", "angle": "Myth-bust: the PIN only ever sends money, which is the trick refund scams rely on.", "why": "Six words, instantly useful, flips a half-held belief. The mechanism is the payoff.", "chosen": true},
     {"hook": "PhonePe में आपका पैसा रखा कहाँ है? कहीं नहीं.", "angle": "Question: apps don't hold money; banks do, and NPCI connects them.", "why": "Good curiosity, but the stakes for the viewer come late.", "chosen": false}
   ]}
   ```
5. **Talk it through.** Write the story as 4–6 plain, connected sentences, the way you'd explain it to a friend, with the person in them (§6). This is the spine of the script, and it's where the value is decided (the value test, §6).
6. **Outline.** Map the spine onto the channel's `format`. Budget the words: `length_seconds × words_per_minute ÷ 60` (60 s at 160 wpm = 160 words). The hook gets ≤ 12 words, each beat one idea and one visual, and no beat runs over ~15 s.
7. **Draft** in the scenes.md format (§6–§7).
8. **Add pictures and sources.** Give the beats about real things (a product, a place, a document, a person's role, the moment itself) a photo, following [images.md](images.md), and add a `Source:` line to beats that state a fact from the notes (§7).
9. **Time it** with `studio.py scenes --script ID`. Get within ±10% of `length_seconds` and fix every warning, including the on-screen ones (§7). To cut, remove whole ideas, not articles and connectives.
10. **Read it aloud and remove the machine.** Go line by line through the table in §6 and §10 and rewrite every match.
11. **Score it** against the rubric (§11). Fix the lowest score first, re-time, and score again. Keep going until every score is ≥ 8. If one can't get there (for example, the notes have no number that would make the stakes concrete), say why and what would fix it.
12. **Save the review** with `studio.py review --script ID --file -`.

## 2. The angle

The topic is what the video is about. The angle is why anyone should care.

| Topic (not enough) | Angle |
|---|---|
| How UPI works | Your UPI PIN only ever *sends* money, and refund scams depend on you not knowing that. |
| Compound interest | Your money's last ten years out-earn its first twenty, so quitting early is the expensive mistake. |
| The 50-30-20 rule | You don't need a spreadsheet to budget. You need three numbers, and to move the 20 on salary day. |
| RBI raises UPI Lite limit | You can now pay up to ₹1,000 without a PIN. Here's when that's useful and when to switch it off. |

To find it, ask: what does this audience believe that's wrong? Which number would make them say "wait, what"? What changes for their money, time, safety, or plans? Why now: is there a news peg, a deadline, salary day, or tax season?

**Test:** "After watching, the viewer knows/will ___." If you can't fill that in with 15 words or fewer, you have a topic, not an angle. A news story can have different angles on different channels: the Hindi Shorts channel might want "what to do", while the English one wants "why it happened".

## 3. The person and the moment

Facts explain; people make viewers care. Every explainer worth finishing is about someone: the viewer in a situation they recognise, a real person the story happened to, or the person who decided how things work. Find that person in the story's notes ("The people", "The moment") before you write a hook. If the notes have none, research it ([story.md](story.md)); don't make one up.

**Choose who the video is about,** strongest first:

1. **A real case from the notes:** a person named in reporting, a case described in a regulator's order or a court judgment, a user quoted in a published article. Use only what the source says, and cite it.
2. **The viewer, in a moment:** second person, present tense, a scene they've lived. "You're at the counter, and the shopkeeper turns the QR towards you." "Salary आई, rent गया, और 20 तारीख़ को account में 3 हज़ार बचे हैं."
3. **An openly hypothetical person:** "Say your father gets a call…", "मान लो…". A relationship ("your mother", "a friend in her first job") is fine. Invented names and biographies ("Meet Rahul, 28, from Pune") are not: they're one of the most recognisable AI-script moves there is.
4. **The decision-maker:** who chose this, and why, in their own words from the notes.

**Carry them through.** The person isn't garnish on the hook. Come back to them when the mechanism lands ("so when your father taps Approve, this is what actually happens") and at the payoff, so the ending answers *their* question. A video that opens on a person and then turns into a lecture loses the viewer exactly where the person disappears.

**Put the viewer somewhere.** Scenes beat summaries: the screen with the green button, the hold music, the bill on the fridge, the queue at the bank. Use the lived details in the notes: what the screen says, what it costs next to something familiar, how long it takes. One concrete detail does more than three adjectives.

**Have a point of view.** A person explaining something has a take: what they'd do, what surprised them, what bothers them about a claim. Say it briefly, in the persona's voice, and only where the evidence earns it: "I'd still put it on the kitchen tap first; that's the one that runs all day." "Honestly, the fifty percent bothers me. Nobody's tested it." Without a view, the script is a brochure; with a view the facts don't support, it's an influencer.

**Never fake experience.** Don't write "When I was in college…", "My uncle lost forty thousand this way" or "I tried it for a month" unless the persona really lived it and the user told you so. A made-up anecdote is a fabricated fact. Use a sourced case, or say "say you…".

**Respect the viewer.** Talk to them like a smart friend who hasn't had time to read the fine print: no talking down, no scolding ("you're doing it wrong"), no fear for its own sake. A scam works on careful people too; say so, and the viewer who forwards it to their parents doesn't feel lectured.

**Test:** Could the viewer say who this video was about, and would that person recognise themselves in it? If the honest answer is "it's about compound interest", go back to the notes and find the person.

Before (a topic):
"Compound interest grows your money faster over time. The longer you stay invested, the more you earn."

After (a person, a moment, a view):
"Say you put one lakh away at twenty-five and then genuinely forget about it. By forty-five it has earned about eight and a half lakh. The ten years after that add twenty more. The annoying part is that the first few years feel like nothing's happening."

## 4. Hooks

The hook is the first 1–2 seconds: roughly the first **five spoken words plus the first visual**. Viewers decide before your second sentence ends.

- **Put the payload first.** Your most surprising true thing goes in the first sentence, not after a setup.
- **Specific beats clever.** A number, a name, or a concrete object beats a pun.
- **Voice and screen land together, doing different jobs.** The VO makes the claim and the screen shows the proof (`compare`, `stat`, or `text`). Never open on a `title` card or a logo.
- **It must be true and paid off.** A hook the script doesn't pay off costs you the ending and the viewer's trust.

**Never open with** greetings, the channel name, "In this video…", "Today we'll…", a date or context line ("On 1 October, the RBI issued a circular…"), a definition ("UPI, or Unified Payments Interface, is…"), or a generic question ("Have you ever wondered…").

### Patterns, by `hook_styles`

| Style | Bad | Good (English) | Good (Hinglish) |
|---|---|---|---|
| `question` | "Have you ever wondered how UPI works?" | "Your PhonePe balance. Where is that money actually kept?" | "PhonePe में आपका पैसा रखा कहाँ है? कहीं नहीं." |
| `surprising-stat` | "Compounding can grow your money a lot." | "One lakh, left alone for thirty years at twelve percent, becomes thirty." | "1 lakh को 30 साल छोड़ दो, 12 percent पर. 30 lakh बनते हैं." |
| `myth-bust` | "There are many myths about UPI." | "Your UPI PIN never receives money. Ever." | "UPI PIN डालने से पैसे आते नहीं. सिर्फ़ जाते हैं." |
| `story` | "Let me tell you a story." | "Say you get a call: 'Sir, your refund is ready. Just approve it.'" | "Call आता है: 'Sir, आपका refund ready है, बस approve कर दीजिए.'" |
| `moment` | "Many people struggle to save money." | "It's the twentieth, and your salary account says three thousand." | "20 तारीख़ है, और salary account में 3 हज़ार बचे हैं." |
| `stakes` | "This could affect your finances!" | "If rent eats half your salary, the famous budget rule breaks. Here's the fix." | "किराया आधी salary खा जाता है? तो 50-30-20 आपके लिए नहीं बना. पर…" |
| `contrast` | "Saving vs investing: what's the difference?" | "Your money's last ten years can out-earn its first twenty." | "Cheque देने पर signature लगता है, लेने पर नहीं. UPI PIN भी वैसा ही है." |

A `story` hook needs a real person or case from the notes, or it must be openly hypothetical ("Say you…", "मान लो…"). Never invent a "Ramesh from Pune". A `moment` hook drops the viewer into a scene they've lived, in the present tense, and the script explains it (§3).

### Before → after

- "Hello friends! Today we're going to talk about something really important: compound interest." → "Your money's last ten years can out-earn its first twenty."
- "दोस्तों, आज हम बात करेंगे UPI fraud के बारे में, जो आजकल बहुत बढ़ गया है." → "UPI PIN डालने से पैसे आते नहीं. सिर्फ़ जाते हैं."
- "The 50-30-20 rule is a popular budgeting framework." → "बजट बनाने के लिए स्प्रेडशीट नहीं चाहिए. बस तीन नंबर: पचास, तीस, बीस."

**Hook check:** Does it contain a concrete noun or number? Is its question answered later in this script? Would you say it out loud to a friend? Could a rival channel paste it onto a different topic? If so, it's generic.

## 5. Retention

Viewers leave when they stop wanting the next sentence. Structure the script so there is always something they're waiting for.

- **Open a loop and close it late.** The hook raises a question, and the payoff answers it near the end, not in beat two. In `english-60s.md`, "why would the last ten years earn more than the first twenty?" is answered piece by piece (each year's return is added to the balance, the doublings get bigger) and landed by the last line: "if you're five years into an SIP and bored, you're still in the slow part."
- **Re-hook every 8–12 seconds** (about 20–30 words). A re-hook is a turn. Vary the move:
  - the catch: "But this fifty percent is Jaquar's own number. Nobody has tested it yet."
  - the next question: "Bank पैसा निकालने से पहले पूछता है: ये आप ही हो?"
  - a reveal: "By year thirty, that same twelve percent adds over three lakh in a single year."
  - an escalation: "QR में भी यही trick है."
  - a shift to "you": "पैसे चले गए? तुरंत 1930 पर call करो."
- **One idea per beat.** If a beat says "and also", split it. Each new beat is a new scene, so splitting gives you a visual change for free.
- **Go back to the person.** Each return to the person from the hook is a re-hook for free: "So back to that call. The moment he taps Approve…"
- **Make the stakes concrete for the viewer.** "Your finances" is abstract; "your ₹12,000 a month" is not. "Fraud is rising" is a statistic; "पैसे आने की जगह account से निकल गए" is a gut punch.
- **Tie pattern interrupts to visual changes.** Change the scene type at least every two beats. A photo after two charts, or a chart after a photo, resets attention. Move from an abstract point to a number, or from a number to a "you".
- **End on the payoff, not a summary.** The last line answers the opening question in a form people would repeat, ideally back with the person you opened on, now knowing something they didn't.
  - Summary (bad): "So that's how compounding works: returns on returns, the Rule of 72, and starting early."
  - Payoff (good): "So if you're thinking of stopping your SIP after a few dull years, remember the money hasn't hit the steep part yet."
- **Make Shorts and Reels loop.** Write the last spoken line so it runs back into the first: "So if you're five years into an SIP and bored, you're still in the slow part." → "One lakh at twelve percent earns more in its last ten years than in its first twenty." Add a `Note:` so the editor knows.
- **Use one CTA, specific and short, after the payoff.** "ये Reel उसे भेजो जो हर refund approve कर देता है" beats "like, share and subscribe".

## 6. Sound like a person

The voiceover is heard once, at speed, often with half the viewer's attention. It has to sound like one person explaining something they understand to one friend. Most AI scripts fail here, not on facts: they're written as a string of slogans, and viewers hear it within two lines.

**Draft by talking it through.** Before writing beats, explain the story out loud (or in plain prose) the way you'd tell a friend over chai, in 4–6 sentences: what happened, why it works that way, what it means for them. That paragraph is the spine. Then cut it into beats and tighten it. Don't write beat by beat from a blank page; that's what produces disconnected one-liners.

- **Connect the sentences.** People explain with links: "so", "because", "which means", "that's why", "but", "and then". Each sentence should lead into the next. If you could shuffle the sentences in a beat without anyone noticing, they aren't connected.
- **Mostly full sentences, 8–16 words.** Use one clause and put the verb early. Short sentences are for emphasis, so they only work when they're rare: at most one or two in the whole script.
- **Use contractions and plain words:** it's, you'll, don't, that's; "use" not "utilize", "about" not "approximately".
- **Cut written-only devices:** parentheses, semicolons, "respectively", "the former", "e.g.", and lists of more than three things inside a sentence.
- **Say it like you'd say it.** Asides and small reactions are human ("which, honestly, surprised me", "हाँ, ये भी गिनती में आता है", "which is a lot, for a tap"). One or two per script, in the persona's voice.
- **Use the audience's words.** The notes list what people actually ask ("What people believe, and what they ask"). Use their phrasing for the question you answer: "Is the cashback actually worth it?" not "Let's evaluate the cashback proposition".
- **Talk to one person.** "You", never "guys", "everyone", "viewers" or "all of you". The viewer is alone with their phone.
- **Let it land.** After the number that matters, give it a moment instead of rushing to the next sentence: end the beat there, and start the next one with a turn. A `Duration:` a second longer than the words need is how a person pauses.
- **Read every line aloud at speaking speed.** Rewrite anything you stumble on, need a breath in the middle of, or that sounds like a press release, a LinkedIn post, or a trailer.

### What makes a script sound machine-made

These patterns are the giveaway, even when every word is true. Find them in your draft and rewrite them.

| Pattern | Sounds like | Say instead |
|---|---|---|
| Fragment chains | "Same money. Same rate. Only time changed." | "You put in the same lakh at the same rate. The only thing that changes is how long it sits there." |
| Setup-reveal crutches | "Here's why." "Here's the catch." "The result?" "The kicker?" "Plot twist:" | Just say the reason, the catch, or the result, joined to what came before: "But this 50% is the company's own number." |
| "Not X. It's Y." reframes | "It's not a tap. It's a water meter." | Say what it is and why that matters. |
| A slogan at the end of every beat | "Slow, then sudden." "That's the runway." "Simple." | At most one quotable line per script, where it lands the payoff. |
| Rhetorical question, instant answer | "So what does this mean? It means…" | Make the point. Real questions are fine when the script answers them later. |
| Threes everywhere | "Fast, cheap, and reliable." "Brush, rinse, repeat." | Use the one or two things that matter. |
| Every line the same length and shape | Seven-word sentence, seven-word sentence, seven-word sentence. | Vary it: a longer explaining sentence, then a short one. |
| Labels instead of speech | "Honest catch: twelve percent is an example." | "Twelve percent here is just an example, not a promise." |
| Empty intensity | "This changes everything." "Let that sink in." "Read that again." | Show the number or the consequence, and let it do the work. |
| Aphorisms and proverbs | "जो बोले scan करो, वो देने नहीं आया." "Time in the market beats timing the market." | Say the plain rule: "पैसे लेने के लिए कुछ scan नहीं करना पड़ता." |
| Borrowed wisdom | "Compound interest is the eighth wonder of the world." (attributed to Einstein, without evidence) | Quote only what a source you opened says, word for word, and name it. |
| Soft hype | "Could quietly turn into lakhs." "A small habit, a big difference." | Give the number and its assumption: "about twenty-nine lakh in twenty years, at an assumed eight percent." |
| Teaser twists | "Haiku beats Mistral. Until it doesn't." "Let's check what those scores actually mean." | State the finding: "Haiku wins on the combined score, and Mistral wins on business workflows." |
| Generic sign-off | "Follow to keep up with AI news." "Follow for more." | Say what the next video gives them: "Follow for one model comparison a week." |
| Invented characters | "Meet Rahul, a 28-year-old from Pune." | A sourced case, the viewer ("you"), or an openly hypothetical relation: "Say your cousin…" (§3). |
| Fake anecdotes | "My friend lost fifty thousand last month." "I tried this for 30 days." | Only true experience of the real persona. Otherwise a sourced case or "say you…". |
| Lecture voice | "It is essential to understand that…" "One must consider…" | Say it to one person: "The thing to know is…" or just the fact. |
| Talking to a crowd | "Hey guys!" "Everyone needs to know this." | Talk to "you". |
| "Imagine…" openers | "Imagine a world where…" "Picture this:" | Put them in the moment directly: "You're at the counter…" |
| Mock suspense | "And what happened next shocked everyone." "Nobody talks about this." | Say what happened. |

Before (machine): "Here's why. You earn returns on your returns. Year one? Twelve thousand. Year thirty? Over three lakh. Slow, then sudden."
After (person): "That's because every year's return is added to the balance, so next year's twelve percent is worked out on a bigger number. In year one that's twelve thousand rupees. By year thirty it's over three lakh, in a single year."

Before: "Compound interest, which refers to the process whereby interest is earned on both the principal and previously accumulated interest, can significantly enhance long-term wealth creation."
After: "You earn returns on your returns. In year one, twelve percent of one lakh is twelve thousand."

### The value test

A viewer who suspects a video is AI keeps watching only if it's worth their time. Before you score, check that the script gives them at least one of these, stated plainly, not hinted at:

- **A number they didn't know** that changes how they see it ("the 50% saving is the maker's own figure; nobody has tested it").
- **How or why something works**, explained so they could explain it to someone else.
- **A decision rule or a check** they can use ("put it on the tap that runs the most"; "if you have to enter your PIN, you're paying").
- **What to do next**, with the real name, number, date, or link ("call 1930", "from 1 November").

Then ask: if someone watched with the sound off, reading only the captions and the screen, would they still get it? And would a person who knows this field nod along, or wince?

### Numbers, said the way people say them

Write the VO the way the number is spoken. The screen carries the exact figure. Numbers spelled out as words count as spoken words, so the timing stays honest.

| On screen | English VO | Hinglish VO | Hindi VO |
|---|---|---|---|
| ₹5,000 | five thousand rupees | 5 हज़ार रुपये | पाँच हज़ार रुपये |
| ₹1,00,000 | one lakh (never "a hundred thousand") | 1 lakh | एक लाख |
| ₹2.5 crore | two and a half crore | ढाई crore | ढाई करोड़ |
| ₹3,21,000 | over three lakh | 3 lakh से ज़्यादा | तीन लाख से ज़्यादा |
| 12% | twelve percent | 12 percent | बारह परसेंट |
| 1 Nov 2026 | November first | 1 November से | एक नवंबर से |

Use lakh and crore, never million or billion, for Indian audiences. Round for the ear ("almost five lakh") and put the precise figure on screen and in the citation.

### Hinglish

Hinglish uses Hindi grammar with the nouns people actually say in English. The verbs, postpositions, and connectives (है, के, को, करो, तो, पर, मतलब) are Hindi, in Devanagari. Words like account, refund, app, scan, approve, rate, salary, EMI, and brands are English, in Latin script (SKILL.md).

- Good: "Scan करके PIN डाला, मतलब पैसे भेजे."
- Romanized (never): "Scan karke PIN daala, matlab paise bheje."
- Over-translated: "स्कैन करके व्यक्तिगत पहचान संख्या डाली."
- English with sprinkles: "When you scan the QR code, then पैसे जाते हैं."
- Compound verbs are natural: "approve कर दो", "check कर लो", "cancel हो गया".
- Pick a register and keep it. "आप + करो" is normal casual speech, but don't swing between तू, तुम, and आप.

### Hindi

Write बोलचाल की हिंदी: what a smart person says out loud, not what a government notice prints. Use शुद्ध Hindi only when the `persona` asks for it.

| Stiff | Spoken |
|---|---|
| आवश्यक | ज़रूरी |
| परंतु / किंतु | पर / लेकिन |
| अतः | इसलिए / तो |
| सहायता | मदद |
| प्रतिशत | परसेंट |
| उपरोक्त | ये / ऊपर वाला |
| आरंभ करें | शुरू करो / करें |

Write everyday loanwords in Devanagari (सैलरी, बजट, फ़ोन, शॉपिंग). Acronyms and brands may stay in Latin script (EMI, UPI, OTT, PhonePe). Use the nuqta where it's standard (ज़रूरत, फ़ोन).

Before: "उपरोक्त नियम के अनुसार आपकी आय का पचास प्रतिशत आवश्यक व्ययों हेतु निर्धारित किया जाना चाहिए."
After: "पचास परसेंट ज़रूरतों के लिए. किराया, राशन, बिजली, EMI."

## 7. Visual thinking

**The VO explains; the screen shows the one thing to remember.** The screen is never a transcript. Test it twice. With the sound off, do the visuals alone tell the skeleton of the story? With your eyes closed, does the VO make sense?

| Scene | Job | Notes |
|---|---|---|
| `stat` | One number that carries the beat | Pick the number viewers would repeat. It animates counting up, so don't use it for phone numbers or years. |
| `compare` | Before/after, A vs B (exactly two) | The best visual for a contrast hook. |
| `bars` | 3–6 values with a shape (growth, ranking) | Use it when the *shape* is the point. Otherwise use `stat`. |
| `list` | Steps, a flow, or reasons (≤ 5 items, ≤ 6 words each) | Good for mechanisms: "आपका app → NPCI → आपका bank → उनका bank". |
| `timeline` | 2–5 dated events | News context. Keep it to the dates that matter. |
| `quote` | A real quote from the notes, with its source | An official saying it beats you saying it. Never paraphrase inside quote marks. |
| `text` | A punchline, a myth, the rule, the takeaway (≤ 8 words) | The line someone would screenshot. |
| `message` | The moment as it appears on a phone: a call, a text, a notification (1–4 lines) | A chat card with the sender and the lines, appearing one by one. For the exact words of a scam call or an SMS from the notes. Label a reconstruction `Text: Example` and a real one with its `Source:`. Never present an invented message as real. |
| `image` | A photo or screenshot, full-screen | For a beat where seeing the thing *is* the point: the product, the place, the screen. Get the image with [images.md](images.md); describe it precisely ("Phone screen showing a UPI collect request with 'Approve'"), not "money concept". |
| `title` | A section break in longer videos | Never as the hook. |
| `end` | Always the last beat | The title is the takeaway or the series name; the `cta` is one action. |

- **One `Visual:` per beat.** Two visuals means two beats.
- **Put real things, and people, on screen.** A beat about a product, a place, an institution, a document, or a person in their role gets an `Image:` line. Hands on a phone, a shop counter, a street, a plumber at work: people make a video feel made by people. On a stat, punchline, quote, list, message, title or end card, the photo sits across the top of the frame on a rounded photo card and the scene sits below it (beside it in wide formats); on a chart it fills the screen behind, veiled; add `| full` to put it full-screen behind any scene. Two to four photos in a 60-second script make it feel produced instead of templated. Beats about pure numbers or ideas are better without one. See [images.md](images.md) for where photos come from.
- **Show the moment.** If the story turns on a call, a text, a screen or a form, show it: a `message` scene for the words, an `image` for the screen. That's the scene viewers recognise from their own lives.
- **Show where facts come from.** A beat that states a fact from the notes gets a `Source:` line with the short name of its source ("RBI circular, 1 Oct 2026", "Jaquar"). It shows small on screen; it's the cheapest trust you can buy.
- **Change the scene type at least every two beats.** A deliberate series (`stat` 50% → `stat` 30% → `stat` 20%) is fine; three unrelated `text` scenes in a row is not.
- **Add a `Text:` overlay only when it brings something the visual lacks:** a twist, a label, a name ("Refund नहीं, collect request"). If it repeats the VO or the visual, delete it.
- **In `bars` and `compare`, write every value in the same unit.** The player animates the bare number, so "₹12,000" vs "₹3.2 lakh" draws 12,000 against 3.2. Write "₹3,21,000", or put the unit in the title ("₹ lakh").
- **Respect the on-screen word limits:** titles under 6 words, labels under 4, list items under 6, overlays under 8.

### On-screen text

The screen is where a generated video gives itself away first: a slogan on every scene, the same line twice, a chart of numbers nobody measured. Each scene must carry information the viewer can read in one second.

- **Every scene shows a fact, not a mood.** A number with its unit, a name, a step, a label. "Slow, then sudden", "Don't quit before the steep part" and "पानी बचाओ, पैसा भी" are slogans; "Years 21–30 earn ₹20.3 lakh" and "सबसे ज़्यादा चलने वाले नल से शुरू करो" are information.
- **At most two `text` scenes per script,** and each one holds a number, a name, or the rule itself. If the beat is a number, use `stat`; if it's a mechanism, `list`; if it's a contrast, `compare`.
- **Never repeat a headline.** The `end` title is the takeaway in new words, not the hook again and not an earlier `text` scene. A loop lives in the voiceover, not in a duplicated screen.
- **Chart only measured or calculated numbers, with their unit.** A maker's claim ("50% less water") is a `stat` with the claim labelled in its context ("Jaquar's claim, untested"), never a bar chart of invented values like "100 vs 50". Put the unit in each value (`₹2 lakh`, `35%`) or name the measure in the title ("Intelligence Index"); no bare numbers, no parenthesised units.
- **Write titles as plain statements in sentence case:** "What ₹1 lakh earns at 12%", not "₹1 LAKH AT 12% (₹ LAKH)" or a label like "The catch". Labels are for the team (`## Beat`), not the viewer.
- **Order a `compare` so the second item is the subject.** It's drawn in the accent: the after, the new product, the true version ("वो कहते हैं: पैसे आएँगे | असल में: पैसे जाएँगे").
- **Run `studio.py scenes`** and fix every warning it prints; they catch the repeats, slogan runs, and unitless charts.

Before (the screen repeats the VO):
```
Year one, twelve percent of one lakh is twelve thousand rupees.
Visual: text | Year one: 12% of ₹1 lakh = ₹12,000
```
After (the screen shows the contrast the VO is building toward):
```
Year one, twelve percent of one lakh is twelve thousand rupees.
Year thirty, the same twelve percent lands on almost twenty-seven lakh. That's over three lakh, in one year. [3]
Visual: compare | What 12% adds in one year | Year 1: ₹12,000 | Year 30: ₹3,21,000
```

## 8. Specificity and accuracy

- **Use only facts from the story's notes**, and cite `[n]` on the line that uses them. If you need a fact the notes lack, verify it from a source you open, add it to the notes with that source, and then use it. Never use a fact from memory.
- **Choose the concrete detail over the abstraction:** "a regulator" → "RBI"; "recently" → "on 1 October"; "a lot of people" → the number in the notes, or drop the claim; "a popular app" → "PhonePe or Google Pay".
- **Label illustrative numbers.** A worked example ("₹1 lakh at 12%") is fine if the math is in the notes and the script says it's an example: "twelve percent is an example, not a promise."
- **Frame uncertain claims honestly:** "RBI expects", "estimates range from X to Y", "the company says". If a point is contested, give both sides in one line. Don't say "because" unless the notes show the cause.
- **Use absolute words only when they're true.** "Never", "always", and "guaranteed" need a source that says so. "PIN is never needed to receive money" is fine because NPCI says it.
- **Don't fake urgency.** "Act now before it's too late!" is out. A real deadline with its date is fine: "1 November से".
- **Don't write numbers the notes can't support.** If you aren't sure of a figure, write the line so it doesn't need one.

## 9. Applying voice settings

`studio.py voice --channel C` gives you the channel's voice. These settings come from the user, and they override this guide's defaults on style. They never override accuracy.

- **`length_seconds`, `words_per_minute`:** the word budget (§1).
- **`hook_styles`:** write hooks only in these styles.
- **`persona`:** who's talking, and to whom. Decide what this person would notice, what asides they'd make, and what they'd never say. The persona shows in choices, not in "As your friendly finance guy…".

### Tone sliders (0–100)

| Slider | Low (0–30) | Mid (31–70) | High (71–100) |
|---|---|---|---|
| `playful` | Straight and factual. No jokes or wordplay. | One light aside or twist per script. | Jokes, callbacks, and irony, but never at the cost of a fact. |
| `casual` | Complete sentences and a measured register, with आप/कीजिए in Hindi. | Conversational, with contractions. | Spoken fragments, slang the audience uses, and "करो" or "dude"-level familiarity. |
| `intensity` | Calm and reassuring. Advice framed as options. | Clear stakes, direct advice. | Urgent, punchy lines and hard imperatives, still with no fake urgency. |

The same line at different settings:
- playful 15: "Twelve percent is an example, not a promise." · playful 85: "Twelve percent is an example. Not a pinky promise from the market."
- casual 15: "Your bank verifies that the request is yours before releasing the money." · casual 85: "Bank पूछता है: भाई, ये तू ही है ना?"
- intensity 15: "It's worth checking the request before you approve it." · intensity 85: "Don't approve it. Not once. Not for anyone."

### The rest

- **`do` / `dont`:** hard rules. Check every line against them before scoring `voice`.
- **`open`:** the channel's signature opener. Put it right after the hook line, never before, unless it is itself a hook.
- **`close`:** the last spoken line, or the line just before the CTA. Adapt the grammar, keep the meaning.
- **`cta`:** the `end` scene's call to action, and the spoken CTA if there is one. If it's empty, write one specific CTA.
- **`examples`:** the user's real voice, and the best guide you have. Study them for sentence length, vocabulary, the Hindi/English balance, how they open and close, and their humour level. The `why` field tells you what the user values. Match their rhythm; **never copy their facts, lines, or structure wholesale.** Where an example and a slider seem to disagree, the example shows what the user means by the slider.

## 10. Banned: AI-isms and clichés

These phrases mark a script as machine-made or lazy. Don't use them, even "ironically".

| Banned | Do instead |
|---|---|
| "Let's dive in" / "Let's get into it" / "Without further ado" | Start with the first fact. |
| "Have you ever wondered…?" / "Did you know…?" (as an opener) | Ask a specific question, or state the surprising thing. |
| "In today's fast-paced world" / "In this digital age" | Cut it. Give the date or the news peg if one matters. |
| "game-changer", "revolutionize", "seamless", "cutting-edge" | Say what changed and by how much. |
| "unlock", "delve", "leverage", "navigate the landscape", "in the realm of", "tapestry", "ever-evolving" | Use the plain verb: use, look at, works in. |
| "It's important to note that" / "It's worth mentioning" | Just say it. If it matters, it gets its own beat. |
| "plays a crucial role", "a testament to" | Say what it does. |
| "It's not just X, it's Y" | Say Y. |
| "Whether you're a student or a professional…" | Pick the viewer and talk to them. |
| "The answer might surprise you" / "Here's everything you need to know" | Give the surprising answer. |
| "But wait, there's more" / "Stay tuned" / "Buckle up" | Use a real re-hook (§5). |
| "In conclusion" / "To sum up" / "So that's it" | Land the payoff. |
| "Like, share and subscribe" / "Smash that like button" | One specific CTA. |
| "नमस्कार दोस्तों" / "हेलो दोस्तों" / "दोस्तों आज हम बात करेंगे…" | Start with the hook. |
| "तो चलिए शुरू करते हैं" / "आज की इस वीडियो में" | Cut it. |
| "आपको बता दें कि" / "गौरतलब है कि" / "जानिए पूरी खबर" | News-anchor filler. Say the fact. |
| "महत्वपूर्ण भूमिका निभाता है" | Say what it does. |
| "वीडियो को अंत तक ज़रूर देखें" | Earn the ending with an open loop. |
| "बहुत ही ज़्यादा important है" | Show why with a number or a consequence. |
| "उम्मीद है आपको ये जानकारी पसंद आई होगी" / "चैनल को subscribe करना न भूलें" | End on the payoff and one CTA. |

Also see the table of machine-made patterns in §6. Watch for these too: three-adjective lists ("fast, secure, and convenient"), every sentence opening with "So" or "And", a run of rhetorical questions each answered by "The answer? …", em-dash pile-ups, and "Imagine…" openers.

## 11. The rubric

Score each dimension as an integer from 1 to 10. The anchors below define 3, 6, 8, and 10; the scores in between are in between.

| | 3 | 6 | 8 | 10 |
|---|---|---|---|---|
| **hook** | A greeting, context, a definition, or a generic question. | A relevant fact, but vague, or the payload arrives after 3 s. | A concrete, true payload in the first ~5 words, with a visual that lands it. It opens a question the script pays off. | A line the audience would repeat. Hard to scroll past, and VO + screen land it in one second. |
| **clarity** | The viewer couldn't state the takeaway. Jargon goes unexplained. | The takeaway is stateable, but beats wander or carry two ideas. | One idea per beat, every term explained in passing. A 15-year-old in the audience could retell it. | A complex mechanism feels obvious. Nothing to cut. |
| **retention** | Front-loaded. A flat middle, and it ends on a summary. | Some turns, but a stretch of 15 s or more with no new question or visual change, and a weak ending. | A re-hook every ~8–12 s, the open loop paid off at the end, a new visual each beat, a payoff ending. | Every beat raises the next question. It loops, and no beat could be dropped. |
| **specificity** | Abstractions: "significant", "experts say", "many people". | Some numbers, but generic examples and abstract stakes. | Every beat has a concrete number, name, date, place, or image from the notes. The stakes are in the viewer's terms. | So specific it could only be about this story. |
| **voice** | Generic AI voice, banned phrases, wrong language or script rules. | The right language and roughly the right tone, but lines that read as written, not said. Stiff Hindi, or a missed `do`/`dont`. | Sounds like the persona saying it aloud. Sliders, `do`/`dont`, and `open`/`close`/`cta` applied. Reads aloud without a stumble. | Indistinguishable from the channel's best `examples`. |
| **human** | An abstract topic. No person, no moment, no point of view; facts recited in order. | A "you" or a case appears in the hook, then disappears into a lecture. Or a person is invented (a named stranger, a fake anecdote). | The video is about someone: a sourced case, the viewer in a moment they recognise, or an openly hypothetical relation, carried through to the payoff. At least one lived detail from the notes. The persona's view is stated once and earned. | The viewer feels it's about them or someone they know, and would forward it to that person. The ending returns to the person, changed by what they learned. |
| **natural** | Reads like a model: fragment chains, "Here's why", a slogan per beat, labels like "Honest catch:". | Mostly connected speech, but a few §6 patterns remain, or every line has the same shape. | No §6 or §10 patterns. Sentences connect, the rhythm varies, and it sounds like one person talking to one friend. | You couldn't tell it from the channel's best human-made video. |
| **value** | The viewer learns nothing they couldn't guess from the title. | One useful fact, but no mechanism, decision rule, or next step. | Passes the value test (§6): a non-obvious number, a mechanism, or a rule or action the viewer can use, stated plainly. | Something the viewer will act on or repeat, and they'd feel the minute was well spent even if they suspected AI. |
| **accuracy** | Claims not in the notes, or wrong. | Everything is in the notes, but some lines are uncited or overstated (certainty, causation). | Every factual line cited, numbers match the notes, uncertainty framed honestly, illustrative numbers labelled. | All of 8, plus caveats that make the video more trustworthy without slowing it down. |

**The bar is ≥ 8 on every dimension before you save.** Accuracy below 8 is never acceptable: fix it, don't explain it. If another score can't reach 8, say exactly why in `notes` and the summary, and what would fix it (for example, "the notes have no figure for how many users this affects; research NPCI monthly data").

**Score honestly.** The review is for the user: it tells them whether to trust the draft and where to look. Score as a skeptical editor who didn't write it. First drafts usually land at 5–7. A 9 or 10 needs a reason in `notes`. Inflated scores are a failure, worse than a low score, because they hide the problems. Each note names a beat and a problem; "could be punchier" is not a note.

```json
{"scores": {"hook": 9, "clarity": 8, "retention": 8, "specificity": 8, "voice": 8, "human": 8, "natural": 8, "value": 9, "accuracy": 9},
 "summary": "Myth-bust hook, mechanism in two beats, 1930 helpline as the action. 62 s against a 60 s target.",
 "notes": ["Hook: 6 words, flips a common belief; the screen shows the consequence, not the VO.",
           "Retention: 'If it happens' doesn't raise a new question; acceptable because it's the action step.",
           "Accuracy: the app→NPCI→bank flow is simplified (PSP banks omitted); fine for this audience, cited [1].",
           "Voice: आप with करो throughout, matching the elder-sibling persona; no banned phrases.",
           "Human: opens on 'मान लो पापा के phone पर call आता है' and returns to him at the Approve beat and the payoff; 8, not 9, because there's no sourced real case.",
           "Natural: rewrote 'PIN = signature' from three fragments into two connected sentences.",
           "Value: the rule 'if you have to do something to receive money, stop' is usable on the spot; 9."]}
```

## 12. Text posts (`kind: post`)

The same principles apply, compressed. You still do the angle, 2–3 hooks saved with `studio.py angles`, and a review. In a post, `retention` means "does each paragraph earn the next one?"

- **It's still about someone.** The person or moment from §3 gets a sentence of its own, usually the second paragraph: the call, the counter, the salary day.
- **The first line is the hook,** in `*bold*`. WhatsApp previews show only the first line or so, so it must carry the surprising fact or the stake, not a label. "*UPI PIN never receives money. Only sends it.*" beats "*UPI Safety Tips*".
- **Make it scannable:** 2–3 paragraphs of 1–2 sentences each, one idea per paragraph. Numbers and names, not adjectives.
- **Add a one-line takeaway** in `_italic_`: what to do or remember.
- **Sources go last,** as 1–3 plain URLs from the notes. The post must stand alone.
- Use WhatsApp formatting only (`*bold*`, `_italic_`): no headings, no markdown links, and one emoji at most. The language rules are the same as for video. Numbers can be digits here (₹5,000); it's read, not heard.

Before:
```
*UPI Safety Tips* 🔐💡
In today's digital world, UPI fraud is increasing. It's important to note that you should never share your PIN. Stay safe! 🙏
```
After:
```
*UPI PIN डालने से पैसे आते नहीं. सिर्फ़ जाते हैं.*

"Sir, refund भेजा है, बस approve कर दो." ये collect request है. PIN डाला, तो पैसे आपके account से जाएँगे.

QR भी ऐसा ही है: scan करके PIN डालना मतलब payment करना.

_पैसे आने के लिए कुछ नहीं करना पड़ता. कुछ करना पड़े, तो रुक जाओ._
Fraud हुआ? तुरंत 1930 पर call करो.

https://www.npci.org.in/what-we-do/upi/product-overview
https://cybercrime.gov.in
```
