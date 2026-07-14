#!/usr/bin/env python3
"""Grounding check: verify each model's `evidence` quote actually occurs in the
source text.

Motivation: a model that answers from memory (instead of the provided source)
produces evidence quotes that are NOT in the document. This flags such runs
automatically — a low grounding rate means the model did not read/use the
source, so its verdicts are not valid for this benchmark.

Heuristic: normalise whitespace; split each evidence on ellipsis ("...", "…");
a fragment counts as grounded if it (>= MIN_LEN chars) appears verbatim in the
normalised source. Predictions with null evidence (NOT_ENOUGH_INFO) are skipped.

Usage:
    python scripts/check_grounding.py results/gemini_leg_text01_run.json
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_LEN = 15


def norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/check_grounding.py <results/xxx_run.json>")
    run = json.load(open(sys.argv[1], encoding="utf-8"))
    if isinstance(run, list):
        run = {"model": os.path.basename(sys.argv[1]), "predictions": run,
               "source_doc": "leg_text01"}
    src = norm(open(os.path.join(
        ROOT, "sources", run.get("source_doc", "leg_text01") + ".txt"),
        encoding="utf-8").read())

    checked = grounded = 0
    ungrounded = []
    for p in run["predictions"]:
        ev = p.get("evidence")
        if not ev:
            continue
        checked += 1
        frags = [f for f in re.split(r"\.\.\.|…", ev) if len(norm(f)) >= MIN_LEN]
        ok = bool(frags) and all(norm(f) in src for f in frags)
        if ok:
            grounded += 1
        else:
            ungrounded.append(p["id"])

    rate = grounded / checked * 100 if checked else 0
    print(f"\nModel: {run.get('model')} ({run.get('model_id', 'n/a')})")
    print(f"Grounding: {grounded}/{checked} evidence quotes found in source "
          f"= {rate:.0f}%")
    if ungrounded:
        print(f"  NOT grounded (evidence absent from source): {ungrounded}")
    if rate < 80:
        print("  ⚠️  LOW grounding — model likely answered from memory, not the "
              "provided text. Treat this run as INVALID.")


if __name__ == "__main__":
    main()
