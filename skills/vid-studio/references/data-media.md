# Evidence, chart data, narration, and assets

Read when preparing research data, storyboard asset plans, and production assets. Read the approved project preference snapshot for source taste, evidence rules, chart choices, narration/pronunciation, music and captions; apply those choices within the shared factual/data policy. Hyperframes draws and animates supplied content; it does not establish factual truth or automatically furnish valid data.

## Data sources and local records

Use approved websites/feeds/search queries, primary reports/publications, first-party APIs/datasets, and user-provided CSV/JSON/PDF material. Alerts/Trends identify leads; they do not establish a claim by themselves. Record the actual publisher, URL/query, publication and retrieval dates, relevant evidence, and limitations. No invented quotations, numbers, or “trending” status from model memory.

Save original data plus a derived chart-ready dataset under `03-research/data/`. Record extraction and transformation code or explicit calculation steps. A data record needs source IDs, claim IDs, units, population/denominator, coverage dates, missing values, rounding, filters, and transformation notes. APIs are queried during research, never live while rendering. Re-retrieval that changes data needs research and dependent approvals again.

## Chart truth

Every chart has a local specification (template [chart-spec.json](../assets/project/chart-spec.json)): dataset path/hash, claim/source IDs, chart type, units, comparison semantics, domain/baseline, legend or direct labels, uncertainty/forecast treatment, annotation, source note, and reveal behavior.

Length-encoded bars use zero baseline; nonzero line domains must be clear. Incompatible units use separate plots or explicitly reviewed normalization. Preserve scale across comparisons. Keep enough ticks/labels to understand magnitude; minimalism does not justify removing necessary context. Show missing observations honestly, distinguish forecasts/estimates from measurements, and do not interpolate a historical story from one static snapshot. Retain exact final values after the reveal. Inspect registry sample data and independent series scaling before reuse.

## Asset resolution

Resolve each need in order: suitable user-provided local material; available licensed original/real sources; code-authored SVG/HTML diagram/chart; optional approved generated illustration/media. Fetch external files only within authorized scope; freeze local copies with hashes and provenance. Inspect attribution, license/usage terms and material limits. Permission to read a site is not evidence that its imagery can be republished.

For registry/map/effect code, freeze external JS/fonts/textures/geography into local dependencies and review demo content. For generated imagery, retain prompt and tool provenance and avoid presenting it as documentary evidence. Paid APIs, capture tools, provider fallback, model downloads, and uploads need the setup's explicit scope. Use provider-specific local-only controls when available; never assume failed hosted calls cannot fall through to another service.

## Narration and captions

When narration is selected, during setup or storyboard review approve voice route, short sample if available, pronunciations, and number-reading policy. Recorded narration and available local TTS are valid. Hosted TTS is optional under the processing/budget policy; Hyperframes alone is not a voice-model subscription.

Create complete narration only when selected and after storyboard approval. When narration is disabled, derive scene timing from approved on-screen reading holds and visual pacing. Read exact approved meaning, preserving negations, units, and important precision. Pronunciation fixes that alter wording/meaning return to editorial approval. Measure actual audio duration, then derive scene cues and word/phrase timings. Transcription model and language must match the audio; don't select an English-only model for other languages. Correct recognition errors against the approved script, rather than changing the script to fit a transcript.

When captions are selected, review them for names, figures, timing, phrase grouping, glyphs, and phone readability. Emphasize only the words that help understanding. Export separate caption files when the destination needs them; retain available narration word timing locally even when captions are disabled. Don't use estimated word-count timing as final alignment. A fully silent output has no speech alignment or transcription requirement.

## Sound and mix

Music is optional. Keep narration, music, source-video audio, and effects separate. Mute source-video audio when replacing it. Use Hyperframes' documented audio groups, gain, automation envelopes, and supported effect chains; verify JSON/attribute syntax against the pinned audio reference before authoring it.

When a bed competes with narration, use the approved voiceover-carve/ducking approach, then listen for pumping, lost consonants, and distracting effects. Recompute after changing narration or timing. Measure integrated loudness and true peak on the final decoded mix against the approved delivery target. Do not infer quality from gain sliders or peak amplitude alone. If listening cannot be performed by the agent, mark listening QA pending for user review.

## Sources

[Official media resolution](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/media-use/SKILL.md), [audio contract](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/skills/hyperframes-audio/SKILL.md), and [data/maps](https://github.com/heygen-com/hyperframes/blob/affa4d53cf86334c18d0476955fce3f4f73f6a06/docs/prompting/data-and-maps.mdx). Evidence and chart-integrity rules above are vid-studio policies, not claims that registry defaults enforce them.
