#!/usr/bin/env python3
"""Parse Astrologie temp.htm into clean JSON sections for the web viewer."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LABELS = {
    0: "Portrait",
    1: "Calcul du ciel",
    2: "Aspects",
    3: "Dominante",
    4: "Caractérologie",
    5: "Typologie planétaire",
    6: "Astropsychanalyse",
    7: "Planètes en maisons",
    8: "Lune noire",
    9: "Étude karmique",
}


def decode(raw: bytes) -> str:
    for enc in ("cp1252", "latin-1", "utf-8"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("latin-1", errors="replace")


def html_to_textish(chunk: str) -> str:
    chunk = re.sub(r"(?is)<script.*?>.*?</script>", "", chunk)
    chunk = re.sub(r"(?is)<style.*?>.*?</style>", "", chunk)
    chunk = re.sub(r"(?i)<br\s*/?>", "\n", chunk)
    chunk = re.sub(r"(?i)</p>", "\n\n", chunk)
    chunk = re.sub(r"(?i)</h[1-6]>", "\n", chunk)
    chunk = re.sub(r"(?i)<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", chunk)
    chunk = re.sub(r"<[^>]+>", "", chunk)
    chunk = chunk.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    chunk = re.sub(r"\n{3,}", "\n\n", chunk)
    return chunk.strip()


def parse(path: Path) -> dict:
    text = decode(path.read_bytes())
    # drop our injector chrome if present
    text = re.sub(r'(?is)<div id="navdrop".*?</div>', "", text)
    text = re.sub(r'(?is)<div id="sommaire".*?</div>', "", text)
    text = re.sub(r"(?is)<style>.*?</style>", "", text)
    text = re.sub(r"(?is)<script>.*?goSection.*?</script>", "", text)

    # Only capital IndexN anchors (ignore lowercase aliases indexN)
    parts = re.split(r'<a\s+[^>]*name\s*=\s*"Index(\d+)"[^>]*>\s*</a>', text, flags=re.I)
    # Force exact Index spelling after split alternatives
    parts = re.split(r'<a\s+[^>]*\bname\s*=\s*"(Index\d+)"[^>]*>\s*</a>', text, flags=re.I)
    # Filter: keep only groups that are IndexN not indexN — re-split carefully
    parts = re.split(r'(?:<a\s+[^>]*\bname\s*=\s*"Index(\d+)"[^>]*>\s*</a>)', text)

    by_id: dict[int, dict] = {}
    title = "Portrait astral"
    m = re.search(r"(?i)Portrait Astral de\s*([^<]+)", text)
    if m:
        title = "Portrait astral — " + " ".join(m.group(1).split())
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        if n > 9:
            continue
        html = re.sub(r"(?is)</div>\s*$", "", parts[i + 1].strip())
        # drop lowercase alias stubs immediately following
        html = re.sub(
            r'(?is)^\s*<a\s+[^>]*name\s*=\s*"index\d+"[^>]*>\s*</a>\s*',
            "",
            html,
        )
        cand = {
            "id": n,
            "label": LABELS.get(n, f"Section {n}"),
            "html": html.strip(),
            "text": html_to_textish(html),
        }
        prev = by_id.get(n)
        if not prev or len(cand["text"]) > len(prev["text"]):
            by_id[n] = cand
    sections = [by_id[k] for k in sorted(by_id)]
    return {"title": title, "source": str(path), "sections": sections}


def main() -> int:
    src = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else Path.home()
        / "Documents/Astrologie/windows-apps/AstroHoroscope/Astrologie/res/temp.htm"
    )
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name("sections.json")
    data = parse(src)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out, "sections", len(data["sections"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
