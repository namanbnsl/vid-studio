# Directing the screen

The scenes are built to look like a product film: type and data on a plain background, one accent, numbers as the hero, photos in frames, calm motion. They only look that way if the script gives them the right material. This guide is how to write `Visual:`, `Text:` and `Image:` lines so every frame reads in one second and nothing looks generated. Read it with [scenes.md](scenes.md) (the syntax) and script-craft.md §7 (what each scene is for).

## The one-second test

Pause the video on any frame. A viewer should be able to say what it shows in one breath: "₹29.6 lakh after 20 years", "starting at 25 gives 2.4 times more", "three things keep it working". If the frame needs a second look, it has too much on it. Cut words before you cut scenes.

## Pick the scene from the beat's job

| The beat… | Use | Write it like this |
|---|---|---|
| lands one number | `stat` | `stat \| ₹29.6 lakh \| After 20 years \| You paid in ₹12 lakh.` |
| sets two numbers against each other | `compare` with numbers | `compare \| Value at 60 \| Start at 35: ₹48 lakh \| Start at 25: ₹1.15 crore` |
| shows a shape (growth, a ranking) | `bars` | `bars \| Value of the same SIP \| 5 years: ₹3.7 lakh \| … \| 30 years: ₹75 lakh` |
| turns a belief around | `compare` with phrases | `compare \| What the caller says \| They say: money comes in \| Really: money goes out` |
| walks through steps or reasons | `list` | 3 items, 2 to 5 words each |
| needs dates | `timeline` | 3 or 4 dates; the last is where the story is now |
| hinges on a message or call | `message` | the real words, 2 or 3 lines, one reply at most |
| needs the viewer to see a real thing | `image` | a photo where the thing fills the frame |
| quotes an authority | `quote` | the exact words, under 25, with who said it |
| states the rule | `text` | one sentence with one emphasised phrase |
| opens the video | `stat`, `message`, `compare` or `image` | never `title`; the hook needs a payload |
| closes it | `end` | the takeaway in new words, and one action |

## Write numbers the scenes can animate

The `stat` scene sets its number as large as the frame allows and rolls the digits in like an odometer. The `compare` scene works out the difference between two numbers and makes it the headline (`2.4×`, `+38%`, `−20%`). Both only work with clean numbers.

- **Keep a stat value short:** at most 4 digits plus a unit. `₹29.6 lakh`, `42%`, `1.8 crore`, `₹6,500`. `₹29,60,000` is too long to read at a glance. Write lakh or crore, and round to what the viewer needs.
- **A stat's label is the condition and its context is the comparison.** Label: "After 20 years". Context: "You paid in ₹12 lakh. The rest is returns." The label sits above the number in grey; the context sits below it. Neither repeats the number.
- **Give both numbers in a compare the same kind of unit** (₹ and ₹, % and %), so the difference means something. Lakh against crore is fine, because the player converts them. ₹ against % is not.
- **Put the subject second in a compare.** The second value takes the accent, and the headline measures it against the first: `Start at 35: ₹48 lakh | Start at 25: ₹1.15 crore` gives `2.4×`. Reversed, it would read `−58%`.
- **Give every bar the same unit.** The chart shows a shared unit ("lakh") once at its top, so `₹3.7 lakh … ₹75 lakh` reads cleanly. Years and labels go in the label, not the value.
- **A percentage up to 100 also draws a meter.** Use it for shares ("42% of UPI payments"), not for growth ("+42%"), which reads better as a compare.
- **Hold a number long enough to land.** A `stat` or numeric `compare` needs at least 2.5 seconds on screen so the digits settle before the cut. If the voiceover is shorter, add `Duration: 3`.

## Write words the screen can carry

- **Headings are one line, two at most:** 3 to 6 words, a plain statement in sentence case. "Value of the same SIP", not "The Power Of Compounding!".
- **One emphasis per scene.** Wrap the phrase that matters in `*asterisks*` in a `text` scene ("8% is an assumption, *not a promise*"). It takes the accent. Two emphasised phrases cancel each other out.
- **List items are parallel and short:** same grammatical shape, 2 to 5 words, no full stops. "Debit on salary day / Keep going in bad years / Raise it with your pay". Three is the best number. The points arrive one at a time and the earlier ones step back, so each item must make sense alone.
- **Timeline dates are short** ("Age 25", "Oct 2026", "2019") and the labels are under 5 words. The last date takes the accent, so end on the date the story is about.
- **`Text:` labels are rare.** They show as a small accent line above the scene, or on a photo's corner. Use one only to name what the viewer is looking at ("Worked example", "Example message", "Jaquar's claim") or to flag that something is illustrative. Most beats need none; a label on every beat is noise.
- **End titles are 3 to 6 words, and the call to action is one plain sentence** ("Follow for one money calculation a week"). With the default look it shows as an accent text link, so it should read as an invitation, not a slogan.

## Choose photos that suit a frame

Photos appear in three ways. A title's photo fills the frame under a light veil, with the title over it. A photo on most other scenes is a rounded card at the top of the frame, with the scene below it. A photo behind a chart fills the frame and the chart sits over it on frosted glass.

- **One clear subject, with room around it.** A hand on a phone, a shop counter, a street at night. Busy photos with several subjects turn to noise in a card.
- **Prefer wide (landscape) photos for cards**, because the card is wider than it is tall. Tall photos work for the `image` scene and the title.
- **Dark or evenly lit photos for the title**, so the title reads over the veil. A bright sky behind white type fails.
- **Two to four photos in a minute**, on the beats about real things and people. Never two photo beats in a row unless the second is the `image` scene that shows the thing itself.
- **Don't put text in the photo's subject area.** A beat's `Text:` label sits on the photo's bottom-left corner, so choose photos with a quiet corner.

## Pace the scenes

- **Change the scene type every one or two beats.** The film reads as a sequence of different shots. A run of three `stat` scenes is fine only when it's a deliberate series (50% → 30% → 20%).
- **Alternate dense and quiet.** After a chart, give the eye a number, a photo or a line of type. After a `list` or `timeline`, give it a single idea.
- **Open on the payload.** The first scene holds the hook's number, message or contrast. Never open on a `title` or a label.
- **One scene per idea, about 3 to 8 seconds each.** Under 2 seconds the motion can't finish; over 10 the frame goes stale. Split long beats.
- **Let the last scene breathe.** The `end` beat needs 3 seconds or more; add `Duration: 3` if its line is short.

A shape that works for a 60-second explainer:

1. `stat` or `message`: the hook's payload
2. `image`, or a scene with an `Image:` line: the moment, with a person in it
3. `list` or `timeline`: the mechanism
4. `bars` or `compare`: the evidence
5. `quote`: an authority, if the notes have one
6. `text`: the rule, with one emphasised phrase
7. `end`

## Choose the look

When you set up a channel or the user describes a feeling, start from a preset ([look.md](look.md)):

- **Graphite** for anything that should feel like a product film: near-black, one warm accent, Geist, plain captions.
- **Studio White** for the same restraint in light.
- **Night Edition** for an editorial, magazine voice (serif headlines).
- **Monsoon** or **Neon Finance** for Hindi and Hinglish channels; their fonts cover Devanagari.
- **Swiss** for a strict, flat, information-design look.

Keep `cards.style: glass`, which puts type on the background, unless the user asks for visible tiles (`solid`) or the editorial layout (`flat`).

## Before you finish

Run `studio.py scenes --script ID` and fix every warning. Then check each beat against this list:

- Does the frame pass the one-second test?
- Is every number short, unit-matched, and held for at least 2.5 seconds?
- Does every scene show a fact, not a mood (script-craft.md §7)?
- Is there at most one emphasis per scene, and are `Text:` labels rare?
- Does the scene type change every one or two beats?
- Do the photos have one subject and a quiet corner?
