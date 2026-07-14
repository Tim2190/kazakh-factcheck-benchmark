#!/usr/bin/env python3
"""Score a model's idiom-comprehension run (Track B).

Input: a validated grades file. Each idiom gets a human-adjudicated grade for
phase 1 and (only if phase 1 = "unknown") phase 2:
    equivalent | similar | unknown

    {"model": "...",
     "grades": [{"id":1, "phase1":"equivalent", "phase2":null}, ...]}

Scoring (per idiom, max 1.0):
  - solved in phase 1: equivalent=1.0, similar=0.5  (no penalty)
  - only in phase 2  : PHASE2_FACTOR x (equivalent=1.0|similar=0.5|unknown=0.0)

Reports total score, phase-1 knowledge rate, and phase-2 rescue rate.

Usage:
    python scripts/score_idioms.py idioms/results/<model>_grades.json
"""
import json
import sys

GRADE_PTS = {"equivalent": 1.0, "similar": 0.5, "unknown": 0.0}
PHASE2_FACTOR = 0.5


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/score_idioms.py <grades.json>")
    run = json.load(open(sys.argv[1], encoding="utf-8"))
    grades = run["grades"]
    n = len(grades)

    total = 0.0
    p1_known = 0          # solved (fully or partially) in phase 1
    p1_full = 0           # exact equivalent in phase 1
    failed_p1 = 0
    rescued = 0           # of those who failed p1, got it (fully/partially) in p2
    for g in grades:
        p1 = g.get("phase1", "unknown")
        if p1 in ("equivalent", "similar"):
            total += GRADE_PTS[p1]
            p1_known += 1
            p1_full += (p1 == "equivalent")
        else:
            failed_p1 += 1
            p2 = g.get("phase2") or "unknown"
            total += PHASE2_FACTOR * GRADE_PTS[p2]
            rescued += (p2 in ("equivalent", "similar"))

    print(f"\nModel: {run.get('model')}")
    print(f"Idiom score: {total:.2f} / {n}  = {total/n*100:.1f}%")
    print(f"  Phase-1 knowledge: {p1_known}/{n} = {p1_known/n*100:.0f}% "
          f"(exact equivalent: {p1_full}/{n} = {p1_full/n*100:.0f}%)")
    if failed_p1:
        print(f"  Phase-2 rescue: {rescued}/{failed_p1} = {rescued/failed_p1*100:.0f}% "
              f"of the {failed_p1} it didn't know cold")
    else:
        print("  Phase-2 rescue: n/a (nothing failed phase 1)")


if __name__ == "__main__":
    main()
