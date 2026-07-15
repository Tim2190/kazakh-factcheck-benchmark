# Kazakh Language Understanding Benchmark

How well do modern LLMs actually understand **Kazakh** (a low-resource
language)? This benchmark probes it from two complementary angles.

| Track | Ability probed | Task | Data | Status |
|-------|----------------|------|------|--------|
| **A — Fact-checking** | grounded reasoning / reading comprehension | given a source text + a claim, judge SUPPORTED / REFUTED / NOT_ENOUGH_INFO | 60 claims, 3 genres | ✅ complete |
| **B — Idioms** | figurative & lexical competence (closed-book) | give the meaning of a Kazakh idiom; two-phase (with/without a usage example) | 30 idioms | 🔄 in progress |

Five LLMs from five labs are evaluated: **Claude** (Anthropic), **Gemini 2.5
Flash** (Google), **Qwen3.7-Plus** (Alibaba), **DeepSeek-V3**, **Kimi K2.6**
(Moonshot). Only Gemini runs via API (temperature 0); the others via web chat;
Claude via a blind isolated agent. The two tracks are deliberately different:
Track A tests reasoning over *given* evidence, Track B tests *stored* knowledge
of Kazakh phraseology.

---

## Track A — Grounded fact-checking

Low-citation, recently published Kazakh texts are used (models can't answer
from memory — see the grounding gate below). From each text a set of claims is
hand-built: some faithful, some deliberately distorted by a fixed taxonomy,
each with a fixed gold verdict.

**Verdict labels:** `SUPPORTED` (text confirms) · `REFUTED` (text contradicts)
· `NOT_ENOUGH_INFO` (text is silent).

**Distortion taxonomy (`claim_type`):**

| `claim_type` | Gold | What was changed |
|--------------|------|------------------|
| `real` | SUPPORTED | faithful paraphrase |
| `fake_number` | REFUTED | a number/date/quantity altered |
| `fake_entity` | REFUTED | a name/body/role/concept swapped (incl. speaker attribution) |
| `fake_causal` | REFUTED | a cause↔effect / condition↔result relation inverted |
| `fake_invented` | NOT_ENOUGH_INFO | a fully invented statement absent from the text |

**Sources (genres):** `leg_text01` (Constitution, legal, 20) · `news_text1`
(government economic report, 21) · `msgtxt` (informal code-mixed KK/RU messenger
dialogue, 19).

**Run protocol:** open-book, one claim per call (or batched for chat). The model
gets the *entire* source + one claim; gold is never sent. Output: verdict +
(if not SUPPORTED) error type + a verbatim `evidence` quote.

**Grounding gate (validity):** every `evidence` quote must occur verbatim in the
source (`scripts/check_grounding.py`). A model answering from memory produces
quotes absent from the source and is excluded. All five counted models scored
100% grounding; an early trial that did not ingest the text (quoting the *real*
constitution from memory) was caught at ~12% and dropped.

**Result:** all models 92–97%; the ranking is not statistically separable
(overlapping Wilson CIs; McNemar p ≥ 0.375). The one systematic weak spot is
**causal-relation inversions**. Full report → [`RESULTS.md`](RESULTS.md).

## Track B — Idiom comprehension

30 Kazakh idioms (many rare/literary, native-verified). Each has a Russian
meaning-equivalent, a usage example in Kazakh, and its translation.

**Two-phase task:**
1. **Phase 1** — the bare idiom → the model gives its figurative meaning + the
   closest Russian equivalent (or "белгісіз" = don't know).
2. **Phase 2** — only for idioms failed in phase 1: the model sees a usage
   example and infers the meaning from context.

**Grading:** each answer is graded `equivalent` / `similar` / `unknown`. Grades
are **assigned by a human annotator (fluent in Kazakh) as the final authority**;
an LLM produces a first-pass pre-grade that the annotator reviews and corrects.

**Scoring** (`scripts/score_idioms.py`, max 1.0/idiom): phase-1 equivalent=1.0,
similar=0.5; phase-2 (penalty ×0.5) equivalent=0.5, similar=0.25. Reports the
idiom score, phase-1 knowledge rate, and phase-2 rescue rate. This track is
markedly harder than Track A and separates models more.

---

## Repository layout

```
Track A (fact-checking) — repository root
  factcheck_dataset.xlsx        master dataset (hand-edited)
  data/dataset.csv|.jsonl        git-diffable export
  sources/*.txt                  exact source texts fed to models
  prompts/factcheck_prompt_kk.txt, chat_run_<source>.txt
  results/<model>_<source>_run.json   raw outputs (verdict + evidence)
  scripts/run_factcheck, make_chat_prompt, check_grounding, score, leaderboard,
          export_dataset, extract_source, models.json

Track B (idioms) — idioms/
  idioms/idioms_dataset.xlsx, idioms.csv|.jsonl
  idioms/results/<model>_grades.json, *_raw.json
  prompts/idiom_phase1.txt, idiom_phase2.txt
  scripts/make_idiom_prompt.py, score_idioms.py

Shared
  RESULTS.md   LICENSE   CITATION.cff   notebooks/run_in_colab.ipynb (Gemini)
```

Everything except API keys is committed — prompts, per-item raw outputs, data,
and all scripts — so both tracks are reproducible and auditable.

## How to run

```bash
pip install -r requirements.txt
cp .env.example .env      # Gemini key only; other models run via web chat

# Track A
python scripts/export_dataset.py
python scripts/run_factcheck.py --model gemini --batch --source news_text1
python scripts/check_grounding.py results/gemini_news_text1_run.json
python scripts/score.py results/gemini_news_text1_run.json
python scripts/leaderboard.py            # combined table + McNemar

# Track B
python scripts/make_idiom_prompt.py --phase 1          # -> prompts/idiom_phase1.txt
python scripts/make_idiom_prompt.py --phase 2 --ids 2,8,15   # failed idioms
python scripts/score_idioms.py idioms/results/<model>_grades.json
```

Chat models: generate the prompt, paste it into the model's chat, save its JSON
reply to `results/` (Track A) or grade it into `idioms/results/` (Track B).

## License & citation

Dataset/texts/outputs: CC BY 4.0; code: MIT (see [`LICENSE`](LICENSE)). Please
cite via [`CITATION.cff`](CITATION.cff).
