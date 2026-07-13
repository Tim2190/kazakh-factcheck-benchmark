#!/usr/bin/env python3
"""Export the master .xlsx dataset to git-diffable CSV and JSONL.

The .xlsx is convenient for hand-editing, but binary — reviewers can't see
diffs. This produces plain-text mirrors so every dataset change is auditable.

Usage:
    python scripts/export_dataset.py
"""
import csv
import json
import os

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, "factcheck_dataset.xlsx")
OUT_CSV = os.path.join(ROOT, "data", "dataset.csv")
OUT_JSONL = os.path.join(ROOT, "data", "dataset.jsonl")

COLUMNS = [
    "id", "source_doc", "source_passage", "claim_kk", "claim_type",
    "what_changed", "ground_truth",
    "gemini_label", "llama_label", "deepseek_label", "claude_label",
    "correct?",
]


def read_rows():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb.worksheets[0]
    header = [(c.value or "").strip() if c.value else "" for c in ws[1]]
    idx = {name: header.index(name) for name in COLUMNS if name in header}
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r or r[0] is None or not str(r[0]).strip():
            continue
        row = {}
        for name in COLUMNS:
            if name in idx:
                v = r[idx[name]]
                row[name] = "" if v is None else str(v).strip()
            else:
                row[name] = ""
        rows.append(row)
    return rows


def main():
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    rows = read_rows()

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Exported {len(rows)} rows -> {OUT_CSV} and {OUT_JSONL}")


if __name__ == "__main__":
    main()
