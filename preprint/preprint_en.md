# Do Large Language Models Understand Kazakh? A Two-Track Pilot Benchmark

**Timur Seidalin**

*Preprint, version 1.0 (pilot). Data and code: https://github.com/Tim2190/kazakh-factcheck-benchmark*

---

## Abstract

The performance of large language models (LLMs) on Kazakh — a low-resource
language — is poorly characterised, and existing evaluations typically reduce to
a single aggregate score. We hypothesise that "language understanding" is not
one-dimensional, and, within a pilot benchmark, provide evidence supporting this
hypothesis. **Track A (fact-checking)** probes reasoning over a provided text:
given a source and a claim, the model returns a verdict of
SUPPORTED / REFUTED / NOT_ENOUGH_INFO; 60 hand-built claims span three genres
(legal, a news report, and an informal messenger dialogue mixing Kazakh and
Russian). **Track B (idioms)** probes closed-book knowledge of Kazakh
phraseology over 30 idioms in two phases (without context and, on failure, with
a usage example). Five models from five labs (Claude, Gemini 2.5 Flash,
Qwen3.7-Plus, DeepSeek-V3, Kimi K2.6) are evaluated uniformly; in Track A every
counted run passed an automatic grounding check.

The main observation is a **dissociation of abilities** for the studied models.
On Track A all five score 92–97% and are statistically indistinguishable
(overlapping confidence intervals; pairwise McNemar p ≥ 0.375). On Track B
results range from 28% to 82%, and the ranking reorders: the model ranked
second on fact-checking (Kimi, 95%) is last on idioms (28%). A single aggregate
score would, in all likelihood, not have surfaced this difference. We also note
a characteristic failure of weaker models: confidently substituting a real
Russian idiom with the wrong meaning. All materials (prompts, raw model outputs,
grades, data, code) are open. The observations are bounded by the sample size
and model set of this pilot and are not claimed to generalise to LLMs at large.

---

## 1. Introduction

Evaluating LLMs on low-resource languages usually inherits the practice of
English benchmarks: a single score on a single task. This implicitly treats
"model understands language X" as a scalar. For Kazakh, data are scarce, and the
question of what exactly is being measured is rarely problematised.

We separate "understanding Kazakh" into two distinguishable abilities:

1. **Reasoning over a provided text** (grounded reasoning): given a source, judge
   a claim against it. This is closer to fact-verification and reading
   comprehension.
2. **Stored knowledge of the language and culture** (stored knowledge):
   understanding phraseology and figurative expressions — what cannot be derived
   from a provided text, because no text is provided.

Our contribution: (i) a pilot two-track benchmark for Kazakh with open data and
code; (ii) validity controls (a grounding check in Track A, human adjudication
in Track B); (iii) evidence that, within this pilot, the two abilities diverge,
which points to the limitations of a one-dimensional evaluation for the studied
models.

## 2. Related work (brief)

Automatic fact-checking is commonly framed as three-class classification
(supported / refuted / not enough info) against an evidence corpus. Evaluating
phraseological and idiomatic competence is a separate line, sensitive to how
well an expression is represented in training data. To our knowledge, public
benchmarks of this kind for Kazakh are few; this work is a pilot step in that
direction.

## 3. Method

### 3.1 Overview

Five models from five labs are evaluated: **Claude** (Anthropic),
**Gemini 2.5 Flash** (Google), **Qwen3.7-Plus** (Alibaba), **DeepSeek-V3**
(DeepSeek), **Kimi K2.6** (Moonshot). The run mode is hybrid: Gemini via API
with temperature = 0; the others via web chat (free tiers); Claude via an
isolated "blind" agent with no access to the gold answers. The run mode of each
model is recorded in the raw data.

We note that the tasks of both tracks are, by nature, knowledge access and
judgment (verdict classification; reproducing an idiom's meaning) rather than
open-ended generation. We assume that, given this task character, the access
interface (API or web chat) should not materially change the model's algorithmic
behaviour and hence the result; we did not, however, verify this formally and
list the hybrid mode among the limitations.

### 3.2 Track A: fact-checking

**Sources (genres).** Recently published, low-citation Kazakh texts are used to
reduce the chance of answering "from memory": `leg_text01` — the Constitution of
the Republic of Kazakhstan (legal genre, 20 claims); `news_text1` — a government
economic report (news genre, 21); `msgtxt` — an informal messenger dialogue
mixing Kazakh and Russian with colloquial vocabulary (19).

**Distortion taxonomy.** From each text, claims are hand-built: faithful
(paraphrase; gold SUPPORTED) and deliberately distorted by fixed categories —
`fake_number` (a number/date/quantity altered), `fake_entity` (a
name/body/role/concept swapped, including wrong speaker attribution in the
dialogue), `fake_causal` (a cause–effect or condition–result relation inverted);
all three have gold REFUTED. Separately, `fake_invented` (a fully invented claim
absent from the text; gold NOT_ENOUGH_INFO).

**Protocol.** Open-book, one claim per request (batched for chat). The model
receives the **entire** source and one claim; the gold is never sent. Output: a
verdict + (if not SUPPORTED) an error type + a verbatim evidence quote from the
text.

**Grounding gate (validity).** Each evidence quote must occur verbatim in the
source (case-insensitive, allowing for the trimming of speaker labels in the
dialogue). A run whose quotes are absent from the text is deemed invalid. All
five counted models achieved 100% grounding. One trial run in which the text was
apparently not received, and the model quoted the *real* Constitution, was
rejected at ~12% grounding and excluded.

**Metrics.** Three-class accuracy, macro-F1, Cohen's kappa; Wilson confidence
intervals; the pairwise exact McNemar test for model comparison.

### 3.3 Track B: idioms

**Dataset.** 30 Kazakh idioms (many rare, literary); for each, a Russian
meaning-equivalent, a usage example in Kazakh, and its translation. The reference
meanings, Russian equivalents, and usage examples are drawn from Kazakh
lexicographic and phraseological literature (reference and historical
phraseological sources). These sources were historically compiled and verified
by native-speaker lexicographers outside the scope of this study; this concerns
the provenance of the reference, not a multi-rater check organised by us.
Comparison of the model answers against this reference was performed by a single
annotator (the author) — see Limitations.

**Two phases.** Phase 1: the model receives the bare idiom and gives its
figurative meaning and the closest Russian equivalent (or "белгісіз" = don't
know). Phase 2: only for idioms failed in phase 1, the model receives a usage
example and infers the meaning from context.

**Grading.** Each answer is graded `equivalent` / `similar` / `unknown`. The
final grade is assigned by a human annotator (the author, fluent in Kazakh) as
the last authority, using the meanings and equivalents from the lexicographic
sources above as the reference. To speed this up, an LLM produced a first-pass
grade: in phase 1 the annotator reviewed and corrected it per item; in phase 2
the LLM grade was accepted by the annotator without per-item revision. We state
this explicitly so the method matches the fact.

**Scoring** (max 1.0 per idiom): phase 1 — equivalent = 1.0, similar = 0.5;
phase 2 with a ×0.5 penalty — equivalent = 0.5, similar = 0.25, unknown = 0. The
final score is the sum over 30 idioms. We additionally report phase-1 knowledge
and phase-2 rescue.

## 4. Results

### 4.1 Track A (fact-checking, 60 claims)

| Model | Accuracy | 95% CI (Wilson) | macro-F1 |
|---|---|---|---|
| Claude | 58/60 = 96.7% | 88.6–99.1% | 0.970 |
| Kimi K2.6 | 57/60 = 95.0% | 86.3–98.3% | 0.951 |
| Gemini 2.5 Flash | 56/60 = 93.3% | 84.1–97.4% | 0.933 |
| Qwen3.7-Plus | 56/60 = 93.3% | 84.1–97.4% | 0.931 |
| DeepSeek-V3 | 55/60 = 91.7% | 81.9–96.4% | 0.922 |

Confidence intervals overlap substantially; the pairwise exact McNemar test
gives p ≥ 0.375 for all pairs — within this sample, no statistically significant
difference between models was found. 51 of 60 claims were classified correctly
by all five models. The only category with a systematic failure for the studied
models is **causal-relation inversions** (`fake_causal`): from 5/9 (DeepSeek) to
8/9 (Claude, Kimi); the number, entity, invented, and faithful-paraphrase
categories are close to saturation. The informal genre (a code-mixed dialogue)
did not degrade performance in this experiment: all models ≥ 18/19.

The single claim flagged as borderline (`006`; see Limitations) does not change
the picture when excluded from the sample: accuracy becomes Claude 58/59
(98.3%), Kimi and Qwen 56/59 (94.9%), Gemini 55/59 (93.2%), DeepSeek 54/59
(91.5%). The model ordering and the statistical non-separability are preserved,
i.e. the labelling of this item does not affect the conclusions.

### 4.2 Track B (idioms, 30)

| Model | Idiom score | Phase-1 known | Exact (P1) | Phase-2 rescue |
|---|---|---|---|---|
| Claude | 24.75/30 = 82.5% | 26/30 | 22/30 | 2/4 |
| Gemini 2.5 Flash | 22.25/30 = 74.2% | 25/30 | 16/30 | 4/5 |
| Qwen3.7-Plus | 21.50/30 = 71.7% | 21/30 | 14/30 | 9/9 |
| DeepSeek-V3 | 15.50/30 = 51.7% | 16/30 | 9/30 | 9/14 |
| Kimi K2.6 | 8.50/30 = 28.3% | 8/30 | 4/30 | 9/22 |

Differences between models are substantial: the exact-equivalent count in phase
1 falls from 22/30 to 4/30. Weaker models characteristically substitute a real
Russian idiom with the wrong meaning (e.g. Kimi: "прибрать к рукам" → "адская
жара"; DeepSeek: "бездушный" → "разгильдяй"). "Rescue by context" (phase 2)
appears to be a separate ability: Qwen knew fewer idioms cold but inferred the
meaning from a single usage example in 9 of 9 cases, whereas Kimi, given
context, still failed 13 of 22. This pattern is more consistent with the
hypothesis of limited internal phraseological knowledge than with a
prompt-artifact explanation, though the available data are insufficient to
establish the cause conclusively. Some idioms were not identified correctly by
any model even with context (e.g. "айрандай аптап, күбідей күптеп" — "прибрать к
рукам").

### 4.3 Comparing the tracks

The comparison of the two tracks is the main observation of this work.

| Model | Track A | Track B |
|---|---|---|
| Claude | 96.7% | 82.5% |
| Gemini 2.5 Flash | 93.3% | 74.2% |
| Qwen3.7-Plus | 93.3% | 71.7% |
| DeepSeek-V3 | 91.7% | 51.7% |
| Kimi K2.6 | 95.0% | 28.3% |

On fact-checking the studied models are indistinguishable (92–97%); on idioms
they differ by tens of percentage points and the order changes: Kimi is second
on fact-checking and last on idioms (95% → 28%). These data are consistent with
the view that, for the models considered, reasoning over a provided text and
stored knowledge of Kazakh phraseology rely on different abilities; a single
fact-checking score would, in all likelihood, not have surfaced this difference.

## 5. Discussion

A possible practical implication for developers of Kazakh-language applications:
model choice should likely be matched to the task type. Under our experimental
conditions (open-book, with the context provided), the studied models performed
comparably; extrapolating this observation beyond these conditions — for example,
to specific RAG configurations — calls for caution and separate verification.
For scenarios that rely on internal knowledge of the language and culture
(educational applications, work with literary text, conversational assistants),
the differences between the models considered were substantial, and a high
fact-checking score did not guarantee a high idiom score.

The excluded run also illustrates a methodological point: the result depends on
whether the model actually received the source. An automatic grounding gate is a
relatively cheap and reproducible way to reject runs whose answers appear to rest
on memory rather than on the provided text.

## 6. Limitations

- **Small sample** (60 claims / 30 idioms): confidence intervals are wide; the
  Track A ranking is not separable (McNemar n.s.). Track B differences are
  visible but require confirmation on a larger sample; this is a pilot.
- **Single annotator** as the last authority. The Track A gold is
  single-annotated with a `borderline` flag (e.g. `006`). In Track B, phase 1 is
  human-validated per item, phase 2 is LLM-graded and annotator-approved. The
  reference idiom meanings originate from lexicographic sources verified by
  native-speaker lexicographers historically, prior to and outside this study;
  this is distinct from the single-annotator grading of the model answers.
- **One text per genre** in Track A — genre and specific-document effects are
  confounded.
- **Partial presence of idioms in training data**: famous idioms may be
  memorised, rare ones not; this is the intended difficulty gradient, not a
  defect.
- **Hybrid run mode** (API vs web chat) introduces heterogeneity of conditions
  that we record but do not eliminate. Given that the tasks are knowledge access
  and judgment rather than open generation, we assume the interface has limited
  effect on the result, but this assumption was not tested experimentally.
- The observations pertain to the specific versions of the five models at run
  time and do not generalise to LLMs in general.

## 7. Conclusion

We presented a pilot two-track benchmark of Kazakh language understanding. The
results suggest that, within this pilot, fact-checking and knowledge of
phraseology behave as diverging abilities for the studied models: models
indistinguishable on the first task differ by tens of percentage points on the
second, up to a change of order. This points to the limitations of
one-dimensional LLM evaluation for low-resource languages. Natural directions
for future work include increasing the sample and the number of annotators,
adding genres and distortion types, expanding the phraseological set, and
introducing a reproducibility measurement (several runs per model).

## Data and code availability

All materials — prompts, per-system raw outputs (verdict + quote),
human-validated grades, datasets (xlsx + csv/jsonl), and all code (running,
prompt generation, grounding check, scoring, summary tables) — are published in
the repository. Only API keys are excluded. Data and texts are under CC BY 4.0,
code under MIT.

## How to cite

See `CITATION.cff` in the repository.
