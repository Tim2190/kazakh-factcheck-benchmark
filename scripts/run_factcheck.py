#!/usr/bin/env python3
"""Run one LLM as a fact-checker over the benchmark claims (blind).

The model receives ONLY the full source text + one claim at a time. Ground
truth is never sent. Raw responses are saved so anyone can re-score or audit.

Reproducibility notes:
  - temperature is fixed at 0 (see TEMPERATURE) for determinism.
  - the exact prompt template is prompts/factcheck_prompt_kk.txt (versioned).
  - the exact model_id / base_url used is recorded in the output file.

Usage:
    python scripts/run_factcheck.py --model deepseek
    python scripts/run_factcheck.py --model gemini --source leg_text01

Requires the matching key in .env (see .env.example). Reads model registry
from scripts/models.json.
"""
import argparse
import json
import os
import re
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT_FILE = os.path.join(ROOT, "prompts", "factcheck_prompt_kk.txt")
MODELS_FILE = os.path.join(ROOT, "scripts", "models.json")
DATASET_JSONL = os.path.join(ROOT, "data", "dataset.jsonl")
SOURCES_DIR = os.path.join(ROOT, "sources")
RESULTS_DIR = os.path.join(ROOT, "results")

TEMPERATURE = 0
TIMEOUT = 120
MAX_RETRIES = 4


def load_env(path=os.path.join(ROOT, ".env")):
    """Minimal .env loader (no external dependency)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def build_prompt(source_text, claim):
    tmpl = open(PROMPT_FILE, encoding="utf-8").read()
    return tmpl.replace("{SOURCE}", source_text).replace("{CLAIM}", claim)


def extract_json(text):
    """Pull the first JSON object out of a model reply (handles code fences)."""
    if text is None:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def extract_json_array(text):
    """Pull the first JSON array out of a model reply (for --batch)."""
    if text is None:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    m = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ---- provider adapters: each returns the raw assistant text ---------------

def call_openai(cfg, key, prompt):
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model_id"],
        "temperature": TEMPERATURE,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_anthropic(cfg, key, prompt):
    url = cfg["base_url"].rstrip("/") + "/messages"
    payload = {
        "model": cfg["model_id"],
        "temperature": TEMPERATURE,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def call_gemini(cfg, key, prompt):
    url = f"{cfg['base_url'].rstrip('/')}/models/{cfg['model_id']}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": TEMPERATURE},
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


ADAPTERS = {"openai": call_openai, "anthropic": call_anthropic, "gemini": call_gemini}


def call_with_retry(fn, *args):
    delay = 2
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args)
        except Exception as e:  # noqa: BLE001 — record and back off
            if attempt == MAX_RETRIES - 1:
                raise
            sys.stderr.write(f"  retry {attempt + 1} after error: {e}\n")
            time.sleep(delay)
            delay *= 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="key in scripts/models.json")
    ap.add_argument("--source", default="leg_text01", help="source doc id")
    ap.add_argument("--out", default=None, help="output json path")
    ap.add_argument("--batch", action="store_true",
                    help="send full doc + all claims in ONE request (needed for "
                         "free tiers with low daily request caps, e.g. Gemini)")
    args = ap.parse_args()

    load_env()
    models = json.load(open(MODELS_FILE, encoding="utf-8"))
    if args.model not in models:
        sys.exit(f"Unknown model '{args.model}'. Known: {list(models)}")
    cfg = models[args.model]
    key = os.environ.get(cfg["api_key_env"])
    if not key:
        sys.exit(f"Missing API key: set {cfg['api_key_env']} in .env")
    adapter = ADAPTERS[cfg["api_type"]]

    source_text = open(
        os.path.join(SOURCES_DIR, args.source + ".txt"), encoding="utf-8"
    ).read()

    claims = [
        json.loads(line)
        for line in open(DATASET_JSONL, encoding="utf-8")
        if line.strip()
    ]
    claims = [c for c in claims if c.get("source_doc") == args.source]

    predictions = []
    if args.batch:
        from make_chat_prompt import build_batch_prompt
        prompt = build_batch_prompt(source_text, claims)
        try:
            raw = call_with_retry(adapter, cfg, key, prompt)
            arr = extract_json_array(raw) or []
        except Exception as e:  # noqa: BLE001
            raw, arr = f"ERROR: {e}", []
        by_id = {str(p.get("id")).zfill(3): p for p in arr}
        for c in claims:
            p = by_id.get(str(c["id"]).zfill(3), {})
            ok = bool(p)
            predictions.append({
                "id": c["id"],
                "verdict": p.get("verdict"),
                "error_type": p.get("error_type"),
                "evidence": p.get("evidence"),
                "rationale": p.get("rationale"),
                "parse_ok": ok,
                "raw_response": raw if not arr else None,
            })
            print(f"  {c['id']}: {p.get('verdict')}"
                  f"{'' if ok else '  [MISSING IN OUTPUT]'}")
    else:
        for c in claims:
            prompt = build_prompt(source_text, c["claim_kk"])
            try:
                raw = call_with_retry(adapter, cfg, key, prompt)
                parsed = extract_json(raw)
            except Exception as e:  # noqa: BLE001
                raw, parsed = f"ERROR: {e}", None
            rec = {
                "id": c["id"],
                "verdict": (parsed or {}).get("verdict"),
                "error_type": (parsed or {}).get("error_type"),
                "evidence": (parsed or {}).get("evidence"),
                "rationale": (parsed or {}).get("rationale"),
                "parse_ok": parsed is not None,
                "raw_response": raw,
            }
            predictions.append(rec)
            print(f"  {c['id']}: {rec['verdict']}"
                  f"{'' if rec['parse_ok'] else '  [PARSE FAIL]'}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = args.out or os.path.join(RESULTS_DIR, f"{args.model}_{args.source}_run.json")
    result = {
        "model": args.model,
        "model_id": cfg["model_id"],
        "base_url": cfg["base_url"],
        "api_type": cfg["api_type"],
        "temperature": TEMPERATURE,
        "run_mode": "batch" if args.batch else "per_claim",
        "prompt_file": "prompts/factcheck_prompt_kk.txt",
        "source_doc": args.source,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "predictions": predictions,
    }
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nSaved {len(predictions)} predictions -> {out}")


if __name__ == "__main__":
    main()
