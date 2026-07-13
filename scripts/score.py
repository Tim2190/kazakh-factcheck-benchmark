#!/usr/bin/env python3
"""Score a model run against the gold labels.

Reads gold from data/dataset.jsonl (ground_truth + claim_type) and predictions
from a results/*.json file produced by run_factcheck.py (or the same
{"predictions":[...]} shape). Reports verdict accuracy, per-type accuracy,
a confusion matrix, macro-F1, Cohen's kappa, and the secondary error-type
match on REFUTED items.

Usage:
    python scripts/score.py results/deepseek_leg_text01_run.json
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_JSONL = os.path.join(ROOT, "data", "dataset.jsonl")
LABELS = ["SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO"]
TYPE_TO_ERR = {
    "fake_number": "number", "fake_entity": "entity",
    "fake_causal": "causal", "fake_invented": "invented", "real": None,
}


def load_gold():
    gold = {}
    for line in open(DATASET_JSONL, encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        gold[str(row["id"])] = {
            "ground_truth": (row.get("ground_truth") or "").strip().upper(),
            "claim_type": row.get("claim_type") or "",
        }
    return gold


def kappa(pairs):
    """Cohen's kappa between gold and pred verdicts."""
    n = len(pairs)
    if not n:
        return 0.0
    po = sum(1 for g, p in pairs if g == p) / n
    gc = collections.Counter(g for g, _ in pairs)
    pc = collections.Counter(p for _, p in pairs)
    pe = sum((gc[l] / n) * (pc[l] / n) for l in set(gc) | set(pc))
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def macro_f1(pairs):
    f1s = []
    for lab in LABELS:
        tp = sum(1 for g, p in pairs if g == lab and p == lab)
        fp = sum(1 for g, p in pairs if g != lab and p == lab)
        fn = sum(1 for g, p in pairs if g == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/score.py <results/xxx_run.json>")
    run = json.load(open(sys.argv[1], encoding="utf-8"))
    preds = {str(p["id"]): p for p in run["predictions"]}
    gold = load_gold()

    pairs, by_type = [], collections.defaultdict(lambda: [0, 0])
    confusion = collections.defaultdict(int)
    parse_fail = 0
    for cid in sorted(gold):
        g = gold[cid]["ground_truth"]
        p = preds.get(cid, {})
        pv = (p.get("verdict") or "").strip().upper()
        if p.get("parse_ok") is False:
            parse_fail += 1
        pairs.append((g, pv))
        ct = gold[cid]["claim_type"]
        by_type[ct][1] += 1
        by_type[ct][0] += (g == pv)
        confusion[(g, pv)] += 1

    correct = sum(1 for g, p in pairs if g == p)
    total = len(pairs)
    print(f"\nModel: {run.get('model')}  ({run.get('model_id', 'n/a')})")
    print(f"=== VERDICT ACCURACY: {correct}/{total} = {correct/total*100:.1f}% ===")
    print(f"Macro-F1: {macro_f1(pairs):.3f}   Cohen's kappa: {kappa(pairs):.3f}"
          f"   Parse failures: {parse_fail}")

    print("\n-- accuracy by claim type --")
    for ct, (c, n) in sorted(by_type.items()):
        print(f"  {ct:14} {c}/{n} = {c/n*100:.0f}%")

    print("\n-- confusion (gold -> pred) --")
    for (g, p), n in sorted(confusion.items(), key=lambda x: -x[1]):
        tag = "" if g == p else "   <-- MISS"
        print(f"  {g:16} -> {p:16} : {n}{tag}")

    print("\n-- error-type match on REFUTED items (secondary) --")
    ec = en = 0
    for cid in sorted(gold):
        if gold[cid]["ground_truth"] != "REFUTED":
            continue
        exp = TYPE_TO_ERR.get(gold[cid]["claim_type"])
        got = (preds.get(cid, {}).get("error_type") or "").lower() or None
        en += 1
        ec += (got == exp)
        print(f"  {cid}: expected={str(exp):8} got={str(got):10}"
              f" {'OK' if got == exp else 'X'}")
    if en:
        print(f"  -> {ec}/{en}")


if __name__ == "__main__":
    main()
