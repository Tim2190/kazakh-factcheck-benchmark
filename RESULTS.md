# Results — Track A: Fact-Checking (pilot)

Part of the Kazakh Language Understanding Benchmark (see `README.md`). Track B
(idiom comprehension) results are compiled separately once all models are run.


**Scope:** 60 claims over 3 sources of different genres, 5 LLMs from 5 labs.
Open-book protocol (full source + one claim; gold never shown). Every counted
run passed the grounding gate (100% of evidence quotes found verbatim in the
source). Regenerate with `python scripts/leaderboard.py`.

## Sources (genres)

| id | genre | claims |
|----|-------|--------|
| `leg_text01` | Constitution of Kazakhstan (2026, legal) | 20 |
| `news_text1` | government economic report (news) | 21 |
| `msgtxt` | informal messenger dialogue (code-mixed KK/RU slang) | 19 |

Distortion taxonomy: `real`→SUPPORTED; `fake_number`/`fake_entity`/`fake_causal`
→REFUTED; `fake_invented`→NOT_ENOUGH_INFO.

## Leaderboard (60 claims)

| # | Model | Lab | Accuracy | 95% CI (Wilson) | macro-F1 |
|---|-------|-----|----------|-----------------|----------|
| 1 | Claude (blind) | Anthropic | 58/60 = 96.7% | 88.6–99.1% | 0.970 |
| 2 | Kimi K2.6 | Moonshot | 57/60 = 95.0% | 86.3–98.3% | 0.951 |
| 3 | Gemini 2.5 Flash | Google | 56/60 = 93.3% | 84.1–97.4% | 0.933 |
| 3 | Qwen3.7-Plus | Alibaba | 56/60 = 93.3% | 84.1–97.4% | 0.931 |
| 5 | DeepSeek-V3 | DeepSeek | 55/60 = 91.7% | 81.9–96.4% | 0.922 |

The confidence intervals overlap almost completely (all within ~82–99%). With
60 claims the ranking is **not statistically separable** — the largest gap
(Claude 58 vs DeepSeek 55 = 3 items) is within noise. Treat the ordering as
indicative, not a definitive ranking.

## Accuracy by distortion type

| Model | real | number | entity | causal | invented |
|-------|------|--------|--------|--------|----------|
| Claude | 16/17 | 12/12 | 10/10 | **8/9** | 12/12 |
| Kimi | 17/17 | 11/12 | 9/10 | **8/9** | 12/12 |
| Gemini | 16/17 | 11/12 | 10/10 | **7/9** | 12/12 |
| Qwen | 16/17 | 12/12 | 10/10 | **7/9** | 11/12 |
| DeepSeek | 17/17 | 11/12 | 10/10 | **5/9** | 12/12 |

Number, entity, invented (NEI) and faithful paraphrases are **near-saturated**
(≈95–100% for everyone). The only category that separates models is
**`causal` (cause↔effect inversions)** — from 5/9 (DeepSeek) to 8/9
(Claude, Kimi).

## Accuracy by genre

| Model | legal | news | informal (msgtxt) |
|-------|-------|------|-------------------|
| Claude | 19/20 | 20/21 | 19/19 |
| Kimi | 17/20 | 21/21 | 19/19 |
| Gemini | 19/20 | 18/21 | 19/19 |
| Qwen | 19/20 | 19/21 | 18/19 |
| DeepSeek | 18/20 | 19/21 | 18/19 |

**The informal, code-mixed dialogue did not degrade performance** (all models
≥ 18/19). Robustness to register/slang/code-switching is itself a finding.

## Error analysis (item difficulty)

51 of 60 claims were classified correctly by **all five** models. The signal
lives in 9 items:

| claim | type | missed by |
|-------|------|-----------|
| 031 | fake_causal | 4/5 (all but Kimi) |
| 007 | fake_number | 3/5 (Gemini, Kimi, DeepSeek) |
| 006 | real (borderline) | 2/5 (Claude, Qwen) |
| 008 | fake_causal | 2/5 (Kimi, DeepSeek) |
| 035 | fake_causal | 2/5 (Gemini, DeepSeek) |
| 052 | fake_causal | 2/5 (Qwen, DeepSeek) |
| 004 / 025 / 040 | mixed | 1/5 each |

**4 of the top-6 hardest items are causal inversions.** The single hardest
item (031) fooled 4 of 5 models — the source states "infrastructure is built
*for* the project", the claim inverts it to "the project is launched *for* the
infrastructure."

## Key findings

1. **Modern LLMs fact-check Kazakh well when grounded** — 92–97% on formal and
   informal text. For a low-resource language this is a non-trivial baseline.
2. **Causal-relation inversions are the systematic blind spot.** It is the only
   distortion type that discriminates models; DeepSeek is notably weak (5/9).
3. **Robust to informal register.** Colloquial code-mixed (KK/RU) dialogue did
   not hurt accuracy.
4. **Grounding discipline is high** — 100% of evidence quotes across all counted
   runs occur in the provided text (models used the source, not memory). A
   sixth candidate (a chat model that did not ingest the text and quoted the
   *real* constitution from memory) was caught at ~12% grounding and excluded.

## Limitations

- **N = 60** → wide CIs; rankings are indicative. Pairwise McNemar exact tests
  confirm this: **every** model-vs-model p-value is ≥ 0.375 (all ≫ 0.05), so
  no pairwise difference is statistically significant (see `leaderboard.py`).
- **Single annotator**; borderline items reviewed during construction. Claim 006
  ("constitutional law" vs "separate law") remains a genuine borderline where 2
  models reasonably disagreed with the gold. Two other edge cases were fixed
  mid-study: 032 (an unintended past/future tense artifact) and 052 (reworded
  from an invented-element causal into a clean inversion).
- **One text per genre** → genre and specific-document effects are confounded.
- **Hybrid run mode**: Gemini via API (temperature 0), the others via web chat;
  Claude via a blind isolated agent. Recorded per run.

## Reproducibility

Prompt, per-claim raw outputs (verdict + evidence), dataset (xlsx + csv/jsonl),
and all scripts (`run_factcheck`, `make_chat_prompt`, `check_grounding`,
`score`, `leaderboard`) are committed. Only API keys are excluded.
