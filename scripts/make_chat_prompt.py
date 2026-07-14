#!/usr/bin/env python3
"""Build a single copy-paste prompt for a manual (web-chat) run.

For models whose free API cannot take the full source per request, this bundles
the whole source text + all claims for one source into ONE prompt that asks for
all verdicts as a JSON array. Paste it into a chat UI (Gemini, Llama, …), then
save the returned JSON to results/<model>_<source>_run.json and score it.

Usage:
    python scripts/make_chat_prompt.py --source leg_text01
    -> writes prompts/chat_run_leg_text01.txt
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER = """Сен — мұқият фактчекерсің (fact-checker). Төменде БІР ДЕРЕККӨЗ мәтіні және
тексерілуі тиіс {n} ТҰЖЫРЫМ берілген. Әр тұжырымды ТЕК осы дереккөз мәтініне
сүйеніп бағала.

ЕРЕЖЕЛЕР:
- Тек берілген мәтінге сүйен. Сыртқы білімді немесе өз болжамыңды ҚОЛДАНБА.
- Әр тұжырымға вердикт таңда:
  • SUPPORTED — тұжырымды мәтін тікелей растайды.
  • REFUTED — тұжырымға мәтін тікелей қайшы келеді.
  • NOT_ENOUGH_INFO — мәтінде бұл тақырып туралы мүлдем ақпарат жоқ.
- REFUTED болса, error_type көрсет: number (сан/мерзім), entity (атау/орган/ұғым),
  causal (себеп-салдар байланысы). NOT_ENOUGH_INFO болса error_type = "invented".
  SUPPORTED болса error_type = null.
- "evidence" — мәтіннен ДӘЛ дәйексөз (SUPPORTED/REFUTED үшін), NEI болса null.
  Дәйексөзді ойдан ШЫҒАРМА.

Жауапты ТЕК JSON МАССИВІ ретінде, барлық {n} тұжырым бойынша, басқа мәтінсіз бер:
[
  {{"id":"001","verdict":"...","error_type":"...","evidence":"...","rationale":"..."}},
  ...
]
"""


def build_batch_prompt(source_text, claims):
    """Bundle full source + all claims into one JSON-array prompt.

    Shared by the chat-prompt file generator and the runner's --batch mode so
    both paths use an identical prompt.
    """
    lines = [HEADER.format(n=len(claims)), "\n=== ДЕРЕККӨЗ ===\n", source_text,
             "\n\n=== ТҰЖЫРЫМДАР ==="]
    for c in claims:
        lines.append(f'{c["id"]}. {c["claim_kk"]}')
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="leg_text01")
    args = ap.parse_args()

    source_text = open(
        os.path.join(ROOT, "sources", args.source + ".txt"), encoding="utf-8"
    ).read()
    claims = [
        json.loads(line)
        for line in open(os.path.join(ROOT, "data", "dataset.jsonl"), encoding="utf-8")
        if line.strip()
    ]
    claims = [c for c in claims if c.get("source_doc") == args.source]

    prompt = build_batch_prompt(source_text, claims)
    out = os.path.join(ROOT, "prompts", f"chat_run_{args.source}.txt")
    open(out, "w", encoding="utf-8").write(prompt)
    print(f"Wrote {out}  ({len(claims)} claims, {len(prompt)} chars)")


if __name__ == "__main__":
    main()
