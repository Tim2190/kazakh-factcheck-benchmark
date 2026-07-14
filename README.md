# Kazakh Fact-Checking Benchmark

An open benchmark that measures how reliably modern LLMs verify factual claims
**in the Kazakh language**, and on which kinds of distortion they most often
"go blind" or hallucinate.

## Idea

Low-citation, recently published Kazakh source texts are used. From each text a
set of claims is hand-built: some **faithful** (paraphrases of the text), some
**deliberately distorted** by well-defined categories. Each claim has a fixed
gold verdict. Several LLMs are run as fact-checkers over these claims, and their
verdicts are compared against the gold to see how trustworthy they are.

Using a **recently adopted** source (the 2026 Constitution of the Republic of
Kazakhstan) is deliberate: models have not yet "memorized" it, so they must
actually read the provided text rather than recall it. The full text lives in
`sources/leg_text01.txt` — everything in it is treated as authoritative for
scoring.

## Verdict labels

| Label | Meaning |
|-------|---------|
| `SUPPORTED` | The source text directly confirms the claim. |
| `REFUTED` | The source text directly contradicts the claim. |
| `NOT_ENOUGH_INFO` | The text says nothing about the claim's topic. |

## Distortion taxonomy (`claim_type`)

| `claim_type` | Gold verdict | What was changed |
|--------------|--------------|------------------|
| `real` | SUPPORTED | Faithful paraphrase of the text. |
| `fake_number` | REFUTED | A number, term, or quantity was altered. |
| `fake_entity` | REFUTED | A name, body, office, or concept was swapped. |
| `fake_causal` | REFUTED | A cause↔effect / condition↔result relation was inverted. |
| `fake_invented` | NOT_ENOUGH_INFO | A fully invented statement absent from the text. |

Note: `fake_invented` maps to **NOT_ENOUGH_INFO**, not REFUTED — an invented
statement is not "contradicted" by the text, the text is simply silent on it.
Distinguishing "false" from "unaddressed" is one of the hardest behaviours this
benchmark probes.

## Run protocol

- **Open-book, one claim per call.** The model receives the *entire* source text
  plus a single claim. The gold verdict and `claim_type` are **never** sent.
- **Output:** verdict + (if not SUPPORTED) error type + a verbatim `evidence`
  quote from the text. A missing/invented quote on a REFUTED verdict is a
  hallucination signal.
- **Primary metric:** 3-class verdict accuracy (+ macro-F1, Cohen's kappa).
  **Secondary/diagnostic:** error-type match on REFUTED items.
- **Grounding check (validity gate):** every `evidence` quote must occur
  verbatim in the source (`scripts/check_grounding.py`, case-insensitive). A
  model that answers from memory instead of the provided text produces quotes
  absent from the source; such a run is INVALID and excluded. This is a real
  risk: an early trial where the full text was not actually ingested scored
  quotes from the *real* constitution rather than the provided text and was
  caught at ~12% grounding, versus 100% for every counted run.
- **temperature = 0** for API runs (determinism). Hybrid runs (some via API,
  some via web chat because of free tiers) are supported; the run mode of each
  model is recorded in its results file.

## Repository layout

```
factcheck_dataset.xlsx        Master dataset (hand-edited)
data/dataset.csv|.jsonl       Git-diffable export of the dataset (run export_dataset.py)
sources/*.txt                 Exact source texts fed to models (leg_text01, news_text1, …)
prompts/factcheck_prompt_kk.txt   The per-claim fact-checker prompt (Kazakh)
prompts/chat_run_<source>.txt     Bundled prompt for web-chat runs
scripts/models.json           Model registry for API runs (Gemini)
scripts/run_factcheck.py      API runner (per-claim or --batch)
scripts/make_chat_prompt.py   Build the bundled chat prompt for a source
scripts/check_grounding.py    Validity gate: evidence must occur in the source
scripts/score.py              Per-run scoring (accuracy, F1, kappa, confusion)
scripts/leaderboard.py        Combined table across all sources/models
scripts/export_dataset.py     xlsx -> csv/jsonl ; extract_source.py  docx -> txt
results/                      Raw model outputs (verdicts + evidence)
.env.example                  Template for the Gemini key (.env is git-ignored)
```

Everything except the API keys is committed, so the full method — prompt, code,
raw model outputs, scoring — is reproducible and auditable.

## How to run

```bash
pip install -r requirements.txt

cp .env.example .env          # then paste your API keys into .env
python scripts/export_dataset.py                 # refresh csv/jsonl from xlsx
python scripts/run_factcheck.py --model gemini --batch --source news_text1
python scripts/check_grounding.py results/gemini_news_text1_run.json  # validity gate
python scripts/score.py results/gemini_news_text1_run.json
```

Only Gemini is run via API (`scripts/models.json`). The other four models are
run via web chat: generate the prompt with
`python scripts/make_chat_prompt.py --source <name>`, paste
`prompts/chat_run_<name>.txt` into the model's chat, and save its JSON reply to
`results/<model>_<name>_run.json`.

Run `python scripts/leaderboard.py` for the combined table across all sources
(accuracy, Wilson CIs, macro-F1, per-type/per-source breakdowns, and pairwise
McNemar tests). **See [`RESULTS.md`](RESULTS.md) for the full pilot report and
findings.**

## License & citation

Dataset/texts/outputs: CC BY 4.0; code: MIT (see [`LICENSE`](LICENSE)). Please
cite via [`CITATION.cff`](CITATION.cff).

## Models

Five models, each from a different lab, all validated at 100% grounding:
**Claude** (Anthropic, blind subagent), **Gemini 2.5 Flash** (Google, API),
**Qwen3.7-Plus** (Alibaba, chat), **DeepSeek-V3** (chat), **Kimi K2.6**
(Moonshot, chat). Only Gemini runs via API; the rest via web chat with the
`prompts/chat_run_<source>.txt` prompt.

## Current status

- 2 sources: `leg_text01` (Constitution, 20 claims) + `news_text1` (news, 21).
- All 5 models run on both; combined so far: Claude 39/41, Gemini/Qwen/Kimi
  38/41, DeepSeek 37/41. Confidence intervals overlap — with 41 claims the
  ranking is not yet statistically separable; the robust finding is that
  causal-relation inversions are the systematic weak spot.
- Planned: source text 3 (informal, code-mixed) to reach ~60 and add
  discriminating (causal / pragmatic) items, then compile the report.
