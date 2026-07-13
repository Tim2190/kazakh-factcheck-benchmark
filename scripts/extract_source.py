#!/usr/bin/env python3
"""Extract plain text from a source .docx into sources/<name>.txt.

Used so the exact text fed to the models is versioned and auditable, and so
the runner does not depend on parsing .docx at run time.

Usage:
    python scripts/extract_source.py leg_text01.docx
"""
import html
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def docx_to_text(path):
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"</w:p>", "\n", xml)
    text = html.unescape(re.sub(r"<[^>]+>", "", xml))
    text = "\n".join(ln.rstrip() for ln in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/extract_source.py <file.docx>")
    src = sys.argv[1]
    name = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(ROOT, "sources", name + ".txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    text = docx_to_text(src)
    open(out, "w", encoding="utf-8").write(text)
    print(f"Extracted {len(text)} chars -> {out}")


if __name__ == "__main__":
    main()
