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
- **temperature = 0** for API runs (determinism). Hybrid runs (some via API,
  some via web chat because of free tiers) are supported; the run mode of each
  model is recorded in its results file.

## Repository layout

```
factcheck_dataset.xlsx        Master dataset (hand-edited)
data/dataset.csv|.jsonl       Git-diffable export of the dataset (run export_dataset.py)
sources/leg_text01.txt        Exact source text fed to models
leg_text01.docx               Original source document
prompts/factcheck_prompt_kk.txt   The exact fact-checker prompt (Kazakh)
scripts/models.json           Model registry (ids/base_urls; keys via env only)
scripts/run_factcheck.py      Blind multi-provider runner
scripts/score.py              Scoring (accuracy, F1, kappa, confusion)
scripts/export_dataset.py     xlsx -> csv/jsonl
scripts/extract_source.py     docx -> txt
results/                      Raw model outputs (verdicts + evidence)
.env.example                  Template for API keys (.env is git-ignored)
```

Everything except the API keys is committed, so the full method — prompt, code,
raw model outputs, scoring — is reproducible and auditable.

## How to run

```bash
pip install -r requirements.txt

cp .env.example .env          # then paste your API keys into .env
python scripts/export_dataset.py                 # refresh csv/jsonl from xlsx
python scripts/run_factcheck.py --model gemini   # blind run, saves results/*.json
python scripts/score.py results/gemini_leg_text01_run.json
```

Add or point a model at your provider by editing `scripts/models.json`
(`model_id`, `base_url`, and which env var holds its key). Any OpenAI-compatible
host (Together, Groq, OpenRouter, Fireworks, DeepSeek…) works via
`api_type: "openai"`.

## Current status

- 1 source (`leg_text01` — Constitution), **20 claims**, all categories covered.
- Baseline run recorded: **Claude** (blind), 19/20 = 95% verdict accuracy;
  the single miss is `id 006`, a deliberately borderline paraphrase.
- Planned: add source texts 2 and 3, expand and harden the claim set, run
  Gemini and Llama (via Groq), then compile a report.
