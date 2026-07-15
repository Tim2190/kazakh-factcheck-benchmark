# Results — Kazakh Language Understanding Benchmark (pilot)

Two complementary tracks, five LLMs from five labs. See `README.md` for the
setup; regenerate Track A with `scripts/leaderboard.py` and Track B with
`scripts/score_idioms.py`.

## Overview — the headline

| Model | Lab | Track A: fact-checking (60) | Track B: idioms (30) |
|-------|-----|------------------------------|-----------------------|
| Claude | Anthropic | 96.7% | **82.5%** |
| Gemini 2.5 Flash | Google | 93.3% | 74.2% |
| Qwen3.7-Plus | Alibaba | 93.3% | 71.7% |
| DeepSeek-V3 | DeepSeek | 91.7% | 51.7% |
| Kimi K2.6 | Moonshot | 95.0% | **28.3%** |

**The two tracks measure different, weakly-correlated abilities.** On Track A
all five models cluster at 92–97% and are statistically indistinguishable. On
Track B they spread from 28% to 82% — and the ranking reorders: **Kimi is #2 on
fact-checking but last on idioms** (95% → 28%). Grounded reasoning over a given
text and stored knowledge of Kazakh phraseology are not the same competence, and
a single fact-checking score would have hidden this entirely.

---

## Track A — Fact-checking (60 claims, 3 genres)

| # | Model | Accuracy | 95% CI (Wilson) | macro-F1 |
|---|-------|----------|-----------------|----------|
| 1 | Claude | 58/60 = 96.7% | 88.6–99.1% | 0.970 |
| 2 | Kimi K2.6 | 57/60 = 95.0% | 86.3–98.3% | 0.951 |
| 3 | Gemini 2.5 Flash | 56/60 = 93.3% | 84.1–97.4% | 0.933 |
| 3 | Qwen3.7-Plus | 56/60 = 93.3% | 84.1–97.4% | 0.931 |
| 5 | DeepSeek-V3 | 55/60 = 91.7% | 81.9–96.4% | 0.922 |

- CIs overlap; pairwise McNemar p ≥ 0.375 → **no significant difference**.
- Only systematic weak spot: **causal-relation inversions** (`fake_causal`);
  DeepSeek weakest at 5/9. Number/entity/invented and paraphrase are ≈saturated.
- **Robust to informal register**: the code-mixed KK/RU dialogue did not hurt
  (all ≥ 18/19).
- **Grounding gate**: 100% of evidence quotes occur in the source for all five
  counted models; a sixth trial that answered from memory was caught at ~12%.

## Track B — Idiom comprehension (30 idioms, two-phase)

| # | Model | Idiom score | Phase-1 known | Exact (P1) | Phase-2 rescue |
|---|-------|-------------|---------------|------------|----------------|
| 1 | Claude | 24.75/30 = **82.5%** | 26/30 | 22/30 | 2/4 |
| 2 | Gemini 2.5 Flash | 22.25/30 = 74.2% | 25/30 | 16/30 | 4/5 |
| 3 | Qwen3.7-Plus | 21.50/30 = 71.7% | 21/30 | 14/30 | **9/9** |
| 4 | DeepSeek-V3 | 15.50/30 = 51.7% | 16/30 | 9/30 | 9/14 |
| 5 | Kimi K2.6 | 8.50/30 = **28.3%** | 8/30 | 4/30 | 9/22 |

Scoring: phase-1 equivalent=1.0 / similar=0.5; phase-2 (penalty ×0.5)
equivalent=0.5 / similar=0.25. Phase-1 grades were validated per-item by a human
annotator; phase-2 grades are LLM-assigned and annotator-approved.

- **Stored phraseological knowledge varies enormously** (exact-equivalent in
  phase 1: 22 → 4 out of 30). Weak models don't just miss — they *confidently
  hallucinate a real Russian idiom that maps to the wrong meaning* (e.g. Kimi:
  "прибрать к рукам" → "адская жара"; DeepSeek: "бездушный" → "разгильдяй").
- **Context rescue (phase 2) is a separate skill.** Qwen knew fewer idioms cold
  but inferred **9/9** from a single usage example; Kimi, given context, still
  failed 13/22 — a genuine knowledge gap, not a prompting artifact.
- Some idioms defeat everyone: `#8` "айрандай аптап, күбідей күптеп" (subjugate)
  was missed by all five even with context.

---

## Limitations

- **Small N** (60 claims / 30 idioms) → wide CIs; Track A rankings are not
  separable (McNemar n.s.). Track B differences are large but still a pilot.
- **Single annotator** (Kazakh-fluent) as final authority; Track A gold is
  single-annotated with a `borderline` flag (e.g. `006`). Track B: phase-1
  human-validated per item, phase-2 LLM-graded and human-approved.
- **One text per genre** in Track A → genre and document effects confounded.
- **Idioms partly in training data**: famous idioms may be memorized, rare
  literary ones are not — this is the intended difficulty gradient, not a bug.
- **Hybrid run mode**: Gemini via API (temp 0); others via web chat; Claude via
  a blind isolated agent. Recorded per run.

## Reproducibility

Prompts, per-item raw model outputs, human-validated grades, datasets
(xlsx + csv/jsonl), and all scripts are committed; only API keys are excluded.
