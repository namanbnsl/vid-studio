# The fact sheet

Every script is made from something specific: the **findings** it reports (news), or the **idea** it answers (an evergreen question). Before writing, you turn that material into a fact sheet, `scripts/<id>/facts.md`. The script may say only what's on it.

The fact sheet exists to keep the script precise. It is not background reading, a mood board, or a place for everything interesting you found. If a fact isn't about the findings or the idea, it doesn't go on the sheet, and so it can't leak into the script.

## Steps

1. Run `studio.py material --script ID`. It prints the linked findings with their pages, or the idea with the signal behind it, and where the fact sheet goes.
2. **Open every page behind the findings.** Read what each one actually says. The finding's one-line summary is a pointer, not a source: check it against the page, and correct it on the sheet if the page says something different.
3. **Go one step further only where the script would otherwise be wrong or unclear.** The primary document a news report is based on (the circular, the filing, the company's own page), the number the report rounds, the date it leaves vague. Stay on the development itself.
4. **For an idea,** find the answer to its question in reference pages you open: official explainers, the regulator or company, data, a good encyclopedic overview. The question is the boundary: facts that don't help answer it stay off the sheet.
5. Write the sheet (below), always in English. When several scripts share the same findings or idea (one per channel), research once and write the same sheet into each script's folder.

## What goes on it

```markdown
## The point
One sentence: what happened (or the answer to the idea's question), and who it changes things for, as the sources put it.

## Facts
- Jaquar's touchless range starts at ₹6,500. [1]
- The tap runs while hands are under it and stops when they move away. [1]
- Jaquar says the range uses about 50% less water; no independent test is published. [1]

## Numbers
- ₹6,500: starting price [1]
- 50%: water saving, Jaquar's own claim [1]

## Not known yet
What the sources don't say, or dispute. The script must not fill these gaps.

## Quotes
> "Exact words." (Who, where, date) [n]

## Sources
[1] Jaquar, Sensor faucets, 2026-10-08, https://www.jaquar.com/news/sensor
```

- **One fact per line, each with its `[n]`.** A line without a source number doesn't belong on the sheet.
- **Only what a page you opened says.** Not your own knowledge, not what's "usually" true, not a forum post. Forum posts and comment threads are not sources.
- **Who it affects, only as stated.** If a source says who is affected ("borrowers with floating-rate loans"), note it. Don't add a typical person, a scene, a "moment", or how people might feel about it.
- **Quotes are word for word,** with who said it and where. Leave the section out if there are none. Never write dialogue, a call, a chat, or a message that no source printed.
- **Say what's disputed or unknown.** A company's claim is the company's claim; a forecast is a forecast.
- Skip a section you have nothing for; don't pad it.

If the findings turn out to be thin (one press release with one number), say so on the sheet and in your reply. A short, precise video, or a text post, beats a padded one.

**Respect the user's edits.** If `facts.md` already has text, correct and extend it; don't throw it away unless asked.
