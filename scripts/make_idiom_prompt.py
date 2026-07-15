#!/usr/bin/env python3
"""Build the idiom-comprehension prompts (Track B).

Phase 1: bare idiom -> the model gives its figurative meaning and the closest
Russian equivalent (or says it doesn't know). Phase 2: for idioms the model
failed in phase 1, it sees a usage example and infers the meaning from context.

Usage:
    python scripts/make_idiom_prompt.py --phase 1
    python scripts/make_idiom_prompt.py --phase 2 --ids 5,9,14
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDIOMS = os.path.join(ROOT, "idioms", "idioms.jsonl")

P1_HEADER = """Төменде қазақ тіліндегі фразеологизмдер (идиомалар) берілген. Әрбір
идиоманың АУЫСПАЛЫ (астарлы) мағынасын түсіндіріп, оған ең жақын орысша
баламасын (эквивалентін) көрсет.

ЕРЕЖЕЛЕР:
- Сөзбе-сөз аудармасын емес, нақ мағынасын бер.
- Егер идиоманың мағынасын білмесең, "russian_equivalent" өрісіне "белгісіз"
  деп жаз. ОЙДАН ШЫҒАРМА.

Жауапты ТЕК JSON массиві ретінде бер:
[{"id":1,"russian_meaning":"қысқаша орысша түсіндірме","russian_equivalent":"орысша фразеологизм-балама немесе 'белгісіз'"}, ...]

=== ИДИОМАЛАР ===
"""

P2_HEADER = """Төменде қазақ идиомалары және олардың ҚОЛДАНЫЛУ МЫСАЛДАРЫ берілген.
Мысалдағы контекске сүйеніп, әр идиоманың мағынасын және орысша баламасын
анықта.

ЕРЕЖЕЛЕР:
- Мысалдағы қолданысқа қарап мағынасын тұжыр.
- Білмесең, "белгісіз" деп жаз. Ойдан шығарма.

Жауапты ТЕК JSON массиві ретінде бер:
[{"id":1,"russian_meaning":"...","russian_equivalent":"..."}, ...]

=== ИДИОМАЛАР ЖӘНЕ МЫСАЛДАР ===
"""


def load():
    return [json.loads(l) for l in open(IDIOMS, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, choices=[1, 2], default=1)
    ap.add_argument("--ids", default="", help="phase 2: comma-separated ids to include")
    args = ap.parse_args()

    idioms = {d["id"]: d for d in load()}
    if args.phase == 1:
        lines = [P1_HEADER]
        for i in sorted(idioms):
            lines.append(f'{i}. {idioms[i]["idiom_kaz"]}')
        out = os.path.join(ROOT, "prompts", "idiom_phase1.txt")
    else:
        ids = [int(x) for x in args.ids.split(",") if x.strip()]
        if not ids:
            raise SystemExit("phase 2 needs --ids (idioms failed in phase 1)")
        lines = [P2_HEADER]
        for i in ids:
            d = idioms[i]
            lines.append(f'{i}. Идиома: {d["idiom_kaz"]}\n   Мысал: {d["usage_ex_kaz"]}')
        out = os.path.join(ROOT, "prompts", "idiom_phase2.txt")

    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
