#!/usr/bin/env python3
"""Track B leaderboard: aggregate all idiom grade files into one table.

Reads idioms/results/<model>_grades.json and prints idiom score, phase-1
knowledge, exact-equivalent count, and phase-2 rescue for each model, ranked.

Usage:
    python scripts/leaderboard_idioms.py
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "idioms", "results")
PTS = {"equivalent": 1.0, "similar": 0.5, "unknown": 0.0}
PHASE2_FACTOR = 0.5


def score(grades):
    total = p1known = p1full = nfail = rescued = 0
    for g in grades:
        p1 = g.get("phase1", "unknown")
        if p1 in ("equivalent", "similar"):
            total += PTS[p1]
            p1known += 1
            p1full += p1 == "equivalent"
        else:
            nfail += 1
            p2 = g.get("phase2") or "unknown"
            total += PHASE2_FACTOR * PTS[p2]
            rescued += p2 in ("equivalent", "similar")
    return total, len(grades), p1known, p1full, nfail, rescued


def main():
    rows = []
    for p in glob.glob(os.path.join(RESULTS, "*_grades.json")):
        run = json.load(open(p, encoding="utf-8"))
        rows.append((run["model"], score(run["grades"])))
    rows.sort(key=lambda r: -r[1][0])

    print(f"\n{'='*70}\nTrack B — idiom comprehension leaderboard\n{'='*70}")
    print(f"{'model':10}{'score':>14}{'P1-known':>11}{'exact':>8}{'P2-rescue':>12}")
    for m, (total, n, known, full, nfail, resc) in rows:
        rescue = f"{resc}/{nfail}" if nfail else "n/a"
        print(f"{m:10}{total:6.2f}/{n} = {total/n*100:4.1f}%"
              f"{known:>6}/{n}{full:>6}/{n}{rescue:>12}")


if __name__ == "__main__":
    main()
