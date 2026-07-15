#!/usr/bin/env python3
"""Run a model (via API) on the idiom task — Track B.

Phase 1: all idioms; Phase 2: only the ids given (with their usage examples).
Saves raw answers to idioms/results/<model>_phase<phase>_raw.json. Grading
(equivalent/similar/unknown) is done separately by a human annotator.

Usage:
    python scripts/run_idioms.py --model gemini --phase 1
    python scripts/run_idioms.py --model gemini --phase 2 --ids 2,8,15
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_factcheck as rf          # reuse adapters, env, retry, JSON parsing
from make_idiom_prompt import P1_HEADER, P2_HEADER, load

RESULTS = os.path.join(rf.ROOT, "idioms", "results")


def build(phase, ids):
    idioms = {d["id"]: d for d in load()}
    if phase == 1:
        lines = [P1_HEADER] + [f'{i}. {idioms[i]["idiom_kaz"]}' for i in sorted(idioms)]
    else:
        lines = [P2_HEADER] + [
            f'{i}. Идиома: {idioms[i]["idiom_kaz"]}\n   Мысал: {idioms[i]["usage_ex_kaz"]}'
            for i in ids]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--phase", type=int, choices=[1, 2], default=1)
    ap.add_argument("--ids", default="")
    args = ap.parse_args()

    rf.load_env()
    models = json.load(open(rf.MODELS_FILE, encoding="utf-8"))
    if args.model not in models:
        sys.exit(f"Unknown model '{args.model}'. Known: {list(models)}")
    cfg = models[args.model]
    key = os.environ.get(cfg["api_key_env"])
    if not key:
        sys.exit(f"Missing API key: set {cfg['api_key_env']} in .env")
    adapter = rf.ADAPTERS[cfg["api_type"]]

    ids = [int(x) for x in args.ids.split(",") if x.strip()]
    if args.phase == 2 and not ids:
        sys.exit("phase 2 needs --ids (idioms failed in phase 1)")
    prompt = build(args.phase, ids)

    raw = rf.call_with_retry(adapter, cfg, key, prompt)
    parsed = rf.extract_json_array(raw) or []
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, f"{args.model}_phase{args.phase}_raw.json")
    json.dump(parsed, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Saved {len(parsed)} answers -> {out}")
    for a in parsed:
        print(f"  {a.get('id')}: {a.get('russian_equivalent')}")


if __name__ == "__main__":
    main()
