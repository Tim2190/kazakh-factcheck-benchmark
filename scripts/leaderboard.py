#!/usr/bin/env python3
"""Aggregate every model run in results/ into one leaderboard.

Combines a model's predictions across all source docs, scores against the gold
labels in data/dataset.jsonl, and prints a ranked table plus per-claim-type and
per-source breakdowns. Runs in results/quarantine/ are ignored.

Usage:
    python scripts/leaderboard.py
"""
import collections
import glob
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_JSONL = os.path.join(ROOT, "data", "dataset.jsonl")
RESULTS = os.path.join(ROOT, "results")
LABELS = ["SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO"]


def load_gold():
    gold = {}
    for line in open(DATASET_JSONL, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        gold[str(r["id"]).zfill(3)] = {
            "gt": (r.get("ground_truth") or "").strip().upper(),
            "ct": r.get("claim_type") or "",
            "src": r.get("source_doc") or "",
        }
    return gold


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d * 100, (c + m) / d * 100)


def macro_f1(pairs):
    f1s = []
    for lab in LABELS:
        tp = sum(1 for g, p in pairs if g == lab and p == lab)
        fp = sum(1 for g, p in pairs if g != lab and p == lab)
        fn = sum(1 for g, p in pairs if g == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s)


def main():
    gold = load_gold()
    sources = sorted({g["src"] for g in gold.values()})
    types = ["real", "fake_number", "fake_entity", "fake_causal", "fake_invented"]

    models = {}  # model -> {id, preds{id:verdict}}
    for path in sorted(glob.glob(os.path.join(RESULTS, "*_run.json"))):
        run = json.load(open(path, encoding="utf-8"))
        m = run.get("model", os.path.basename(path))
        models.setdefault(m, {"id": run.get("model_id", ""), "preds": {}})
        for p in run["predictions"]:
            cid = str(p["id"]).zfill(3)
            models[m]["preds"][cid] = (p.get("verdict") or "").strip().upper()

    rows = []
    for m, d in models.items():
        pairs = [(gold[c]["gt"], d["preds"].get(c, "")) for c in gold if c in d["preds"]]
        n = len(pairs)
        k = sum(1 for g, p in pairs if g == p)
        lo, hi = wilson(k, n)
        by_type = {t: [0, 0] for t in types}
        by_src = {s: [0, 0] for s in sources}
        for c in gold:
            if c not in d["preds"]:
                continue
            ok = gold[c]["gt"] == d["preds"][c]
            by_type[gold[c]["ct"]][1] += 1
            by_type[gold[c]["ct"]][0] += ok
            by_src[gold[c]["src"]][1] += 1
            by_src[gold[c]["src"]][0] += ok
        rows.append({"model": m, "id": d["id"], "k": k, "n": n,
                     "acc": k / n * 100 if n else 0, "ci": (lo, hi),
                     "f1": macro_f1(pairs), "by_type": by_type, "by_src": by_src})

    rows.sort(key=lambda r: -r["acc"])

    print(f"\n{'='*78}\nLEADERBOARD — combined over {len(sources)} source(s), "
          f"{len([c for c in gold])} claims\n{'='*78}")
    print(f"{'model':16} {'acc':>12} {'95% CI (Wilson)':>18} {'macroF1':>8}")
    for r in rows:
        print(f"{r['model']:16} {r['k']:>3}/{r['n']:<3} {r['acc']:5.1f}% "
              f"{r['ci'][0]:5.1f}–{r['ci'][1]:4.1f}%   {r['f1']:.3f}")

    print(f"\n-- accuracy by claim_type --\n{'model':16}", end="")
    for t in types:
        print(f"{t.replace('fake_',''):>10}", end="")
    print()
    for r in rows:
        print(f"{r['model']:16}", end="")
        for t in types:
            c, nn = r["by_type"][t]
            print(f"{(str(c)+'/'+str(nn)):>10}", end="")
        print()

    print(f"\n-- accuracy by source --\n{'model':16}", end="")
    for s in sources:
        print(f"{s:>14}", end="")
    print()
    for r in rows:
        print(f"{r['model']:16}", end="")
        for s in sources:
            c, nn = r["by_src"][s]
            print(f"{(str(c)+'/'+str(nn)):>14}", end="")
        print()


if __name__ == "__main__":
    main()
