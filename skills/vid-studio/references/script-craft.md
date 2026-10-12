# Script craft

The bar: someone who never planned to watch stays to the end, learns one thing they repeat to a friend, and every claim survives a fact-check. Generic is the failure mode. **If a line could appear in a video about a different topic, cut it.**

The finished examples in `assets/examples/` show that bar: `english-60s.md`, `hinglish-60s.md`, `hindi-45s.md`. Read the one closest to the channel's language before your first draft.

## 1. The process

Do these in order, for every script. Don't skip steps because the topic seems simple; simple topics are where generic scripts come from.

1. **Find the angle.** Write down why this matters to *this* channel's audience *now*, and the single takeaway in 15 words or fewer (§2).
2. **Write 3–5 hooks.** Use different styles from the channel's `hook_styles` and give each one a different angle, not the same angle reworded (§3).
3. **Pick the strongest and save them all.** Say why it wins (the most specific, the most surprising, the best fit for this audience). Save it with `studio.py angles --script ID --file -`:
   ```json
   {"angles": [
     {"hook": "UPI PIN डालने से पैसे आते नहीं. सिर्फ़ जाते हैं.", "angle": "Myth-bust: the PIN only ever sends money, which is the trick refund scams rely on.", "why": "Six words, instantly useful, flips a half-held belief. The mechanism is the payoff.", "chosen": true},
     {"hook": "PhonePe में आपका पैसा रखा कहाँ है? कहीं नहीं.", "angle": "Question: apps don't hold money; banks do, and NPCI connects them.", "why": "Good curiosity, but the stakes for the viewer come late.", "chosen": false}
   ]}
   ```
4. **Outline.** Map beats onto the channel's `format`. Budget the words: `length_seconds × words_per_minute ÷ 60` (60 s at 160 wpm = 160 words). The hook gets ≤ 12 words, each beat one idea and one visual, and no beat runs over ~15 s.
5. **Draft** in the scenes.md format (§5–§6).
6. **Time it** with `studio.py scenes --script ID`. Get within ±10% of `length_seconds` and fix every warning. To cut, remove whole ideas, not articles and connectives.
7. **Score it** against the rubric (§10). Fix the lowest score first, re-time, and score again. Keep going until every score is ≥ 8. If one can't get there (for example, the notes have no number that would make the stakes concrete), say why and what would fix it.
8. **Save the review** with `studio.py review --script ID --file -`.

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

## 3. Hooks

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
| `stakes` | "This could affect your finances!" | "If rent eats half your salary, the famous budget rule breaks. Here's the fix." | "किराया आधी salary खा जाता है? तो 50-30-20 आपके लिए नहीं बना. पर…" |
| `contrast` | "Saving vs investing: what's the difference?" | "Your money's last ten years can out-earn its first twenty." | "Cheque देने पर signature लगता है, लेने पर नहीं. UPI PIN भी वैसा ही है." |

A `story` hook needs a real person or case from the notes, or it must be openly hypothetical ("Say you…", "मान लो…"). Never invent a "Ramesh from Pune".

### Before → after

- "Hello friends! Today we're going to talk about something really important: compound interest." → "Your money's last ten years can out-earn its first twenty."
- "दोस्तों, आज हम बात करेंगे UPI fraud के बारे में, जो आजकल बहुत बढ़ गया है." → "UPI PIN डालने से पैसे आते नहीं. सिर्फ़ जाते हैं."
- "The 50-30-20 rule is a popular budgeting framework." → "बजट बनाने के लिए स्प्रेडशीट नहीं चाहिए. बस तीन नंबर: पचास, तीस, बीस."

**Hook check:** Does it contain a concrete noun or number? Is its question answered later in this script? Would you say it out loud to a friend? Could a rival channel paste it onto a different topic? If so, it's generic.

## 4. Retention

Viewers leave when they stop wanting the next sentence. Structure the script so there is always something they're waiting for.

- **Open a loop and close it late.** The hook raises a question, and the payoff answers it near the end, not in beat two. In `english-60s.md`, "why do the last ten years out-earn the first twenty?" is answered piece by piece and finally landed by "Quit early, and you miss the steep part."
- **Re-hook every 8–12 seconds** (about 20–30 words). A re-hook is a turn. Vary the move:
  - the catch: "Honest catch: twelve percent is an example, not a promise."
  - the next question: "Bank पैसा निकालने से पहले पूछता है: ये आप ही हो?"
  - a reveal: "Year thirty, the same twelve percent adds over three lakh."
  - an escalation: "QR में भी यही trick है."
  - a shift to "you": "पैसे चले गए? तुरंत 1930 पर call करो."
- **One idea per beat.** If a beat says "and also", split it. Each new beat is a new scene, so splitting gives you a visual change for free.
- **Make the stakes concrete for the viewer.** "Your finances" is abstract; "your ₹12,000 a month" is not. "Fraud is rising" is a statistic; "पैसे आने की जगह account से निकल गए" is a gut punch.
- **Tie pattern interrupts to visual changes.** Change the scene type at least every two beats. After two long sentences, drop in a 2–4 word one ("Slow, then sudden."). Move from an abstract point to a number, or from a number to a "you".
- **End on the payoff, not a summary.** The last line answers the opening question in a form people would repeat.
  - Summary (bad): "So that's how compounding works: returns on returns, the Rule of 72, and starting early."
  - Payoff (good): "So the boring early years aren't wasted. They're the runway. Quit early, and you miss the steep part."
- **Make Shorts and Reels loop.** Write the last spoken line so it runs back into the first: "Because your money's best decade is its last." → "Your money's last ten years can out-earn its first twenty." Add a `Note:` so the editor knows.
- **Use one CTA, specific and short, after the payoff.** "ये Reel उसे भेजो जो हर refund approve कर देता है" beats "like, share and subscribe".

## 5. Writing for the ear

The voiceover is heard once, at speed, often with half the viewer's attention. Write it to be said.

- Keep sentences under 15 words, and most under 10. Use one clause and put the verb early.
- Use contractions: it's, you'll, don't, that's.
- Cut written-only devices: parentheses, semicolons, "respectively", "the former", "e.g.", and long lists inside a sentence.
- Vary the rhythm. Use a long sentence, then a short one, and fragments where they work ("Same one lakh. Same rate."). Deliberate repetition is rhythm, not redundancy.
- **Read every line aloud at speaking speed.** Rewrite anything you stumble on, need a breath in the middle of, or that sounds like a press release.

Before: "Compound interest, which refers to the process whereby interest is earned on both the principal and previously accumulated interest, can significantly enhance long-term wealth creation."
After: "You earn returns on your returns. Year one, twelve percent of one lakh is twelve thousand."

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

## 6. Visual thinking

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
| `image` | A real screenshot, photo, or clip | Describe it precisely enough for an editor to find: "Phone screen showing a UPI collect request with 'Approve'", not "money concept". |
| `title` | A section break in longer videos | Never as the hook. |
| `end` | Always the last beat | The title is the takeaway or the series name; the `cta` is one action. |

- **One `Visual:` per beat.** Two visuals means two beats.
- **Change the scene type at least every two beats.** A deliberate series (`stat` 50% → `stat` 30% → `stat` 20%) is fine; three unrelated `text` scenes in a row is not.
- **Add a `Text:` overlay only when it brings something the visual lacks:** a twist, a label, a name ("Refund नहीं, collect request"). If it repeats the VO or the visual, delete it.
- **In `bars` and `compare`, write every value in the same unit.** The player animates the bare number, so "₹12,000" vs "₹3.2 lakh" draws 12,000 against 3.2. Write "₹3,21,000", or put the unit in the title ("₹ lakh").
- **Respect the on-screen word limits:** titles under 6 words, labels under 4, list items under 6, overlays under 8.

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

## 7. Specificity and accuracy

- **Use only facts from the story's notes**, and cite `[n]` on the line that uses them. If you need a fact the notes lack, verify it from a source you open, add it to the notes with that source, and then use it. Never use a fact from memory.
- **Choose the concrete detail over the abstraction:** "a regulator" → "RBI"; "recently" → "on 1 October"; "a lot of people" → the number in the notes, or drop the claim; "a popular app" → "PhonePe or Google Pay".
- **Label illustrative numbers.** A worked example ("₹1 lakh at 12%") is fine if the math is in the notes and the script says it's an example: "twelve percent is an example, not a promise."
- **Frame uncertain claims honestly:** "RBI expects", "estimates range from X to Y", "the company says". If a point is contested, give both sides in one line. Don't say "because" unless the notes show the cause.
- **Use absolute words only when they're true.** "Never", "always", and "guaranteed" need a source that says so. "PIN is never needed to receive money" is fine because NPCI says it.
- **Don't fake urgency.** "Act now before it's too late!" is out. A real deadline with its date is fine: "1 November से".
- **Don't write numbers the notes can't support.** If you aren't sure of a figure, write the line so it doesn't need one.

## 8. Applying voice settings

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

## 9. Banned: AI-isms and clichés

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
| "But wait, there's more" / "Stay tuned" / "Buckle up" | Use a real re-hook (§4). |
| "In conclusion" / "To sum up" / "So that's it" | Land the payoff. |
| "Like, share and subscribe" / "Smash that like button" | One specific CTA. |
| "नमस्कार दोस्तों" / "हेलो दोस्तों" / "दोस्तों आज हम बात करेंगे…" | Start with the hook. |
| "तो चलिए शुरू करते हैं" / "आज की इस वीडियो में" | Cut it. |
| "आपको बता दें कि" / "गौरतलब है कि" / "जानिए पूरी खबर" | News-anchor filler. Say the fact. |
| "महत्वपूर्ण भूमिका निभाता है" | Say what it does. |
| "वीडियो को अंत तक ज़रूर देखें" | Earn the ending with an open loop. |
| "बहुत ही ज़्यादा important है" | Show why with a number or a consequence. |
| "उम्मीद है आपको ये जानकारी पसंद आई होगी" / "चैनल को subscribe करना न भूलें" | End on the payoff and one CTA. |

Watch for these patterns too: three-adjective lists ("fast, secure, and convenient"), every sentence opening with "So" or "And", a run of rhetorical questions each answered by "The answer? …", em-dash pile-ups, and "Imagine…" openers.

## 10. The rubric

Score each dimension as an integer from 1 to 10. The anchors below define 3, 6, 8, and 10; the scores in between are in between.

| | 3 | 6 | 8 | 10 |
|---|---|---|---|---|
| **hook** | A greeting, context, a definition, or a generic question. | A relevant fact, but vague, or the payload arrives after 3 s. | A concrete, true payload in the first ~5 words, with a visual that lands it. It opens a question the script pays off. | A line the audience would repeat. Hard to scroll past, and VO + screen land it in one second. |
| **clarity** | The viewer couldn't state the takeaway. Jargon goes unexplained. | The takeaway is stateable, but beats wander or carry two ideas. | One idea per beat, every term explained in passing. A 15-year-old in the audience could retell it. | A complex mechanism feels obvious. Nothing to cut. |
| **retention** | Front-loaded. A flat middle, and it ends on a summary. | Some turns, but a stretch of 15 s or more with no new question or visual change, and a weak ending. | A re-hook every ~8–12 s, the open loop paid off at the end, a new visual each beat, a payoff ending. | Every beat raises the next question. It loops, and no beat could be dropped. |
| **specificity** | Abstractions: "significant", "experts say", "many people". | Some numbers, but generic examples and abstract stakes. | Every beat has a concrete number, name, date, place, or image from the notes. The stakes are in the viewer's terms. | So specific it could only be about this story. |
| **voice** | Generic AI voice, banned phrases, wrong language or script rules. | The right language and roughly the right tone, but lines that read as written, not said. Stiff Hindi, or a missed `do`/`dont`. | Sounds like the persona saying it aloud. Sliders, `do`/`dont`, and `open`/`close`/`cta` applied. Reads aloud without a stumble. | Indistinguishable from the channel's best `examples`. |
| **accuracy** | Claims not in the notes, or wrong. | Everything is in the notes, but some lines are uncited or overstated (certainty, causation). | Every factual line cited, numbers match the notes, uncertainty framed honestly, illustrative numbers labelled. | All of 8, plus caveats that make the video more trustworthy without slowing it down. |

**The bar is ≥ 8 on every dimension before you save.** Accuracy below 8 is never acceptable: fix it, don't explain it. If another score can't reach 8, say exactly why in `notes` and the summary, and what would fix it (for example, "the notes have no figure for how many users this affects; research NPCI monthly data").

**Score honestly.** The review is for the user: it tells them whether to trust the draft and where to look. Score as a skeptical editor who didn't write it. First drafts usually land at 5–7. A 9 or 10 needs a reason in `notes`. Inflated scores are a failure, worse than a low score, because they hide the problems. Each note names a beat and a problem; "could be punchier" is not a note.

```json
{"scores": {"hook": 9, "clarity": 8, "retention": 8, "specificity": 8, "voice": 8, "accuracy": 9},
 "summary": "Myth-bust hook, mechanism in two beats, 1930 helpline as the action. 62 s against a 60 s target.",
 "notes": ["Hook: 6 words, flips a common belief; the screen shows the consequence, not the VO.",
           "Retention: 'If it happens' doesn't raise a new question; acceptable because it's the action step.",
           "Accuracy: the app→NPCI→bank flow is simplified (PSP banks omitted); fine for this audience, cited [1].",
           "Voice: आप with करो throughout, matching the elder-sibling persona; no banned phrases."]}
```

## 11. Text posts (`kind: post`)

The same principles apply, compressed. You still do the angle, 2–3 hooks saved with `studio.py angles`, and a review. In a post, `retention` means "does each paragraph earn the next one?"

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
