#!/usr/bin/env python3
"""Keep Horoscope TWebBrowser visible+refreshed inside Wine (no Firefox).

- sizes one Shell Embedding to fill the Horoscope dialog
- unmaps duplicate embeds (black overlays)
- sends F5 so Gecko reloads temp.htm after we rewrite it
"""
from __future__ import annotations

import re
import subprocess


def sh(*args: str) -> str:
    try:
        return subprocess.check_output(args, text=True, errors="replace").strip()
    except Exception:
        return ""


def parse_wins(tree: str):
    for line in tree.splitlines():
        m = re.search(
            r"(0x[0-9a-f]+)\s+\"([^\"]*)\":\s+\(\"(horoscope[^\"]*)\"\s+\"[^\"]*\"\)\s+"
            r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)",
            line,
            re.I,
        )
        if not m:
            continue
        yield {
            "id": m.group(1),
            "title": m.group(2),
            "w": int(m.group(4)),
            "h": int(m.group(5)),
            "x": int(m.group(6)),
            "y": int(m.group(7)),
        }


def xdo(*args: str) -> None:
    subprocess.run(
        ["xdotool", *args],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def refresh_once() -> bool:
    tree = sh("xwininfo", "-root", "-tree")
    wins = list(parse_wins(tree))
    if not wins:
        return False

    dialogs = [
        w for w in wins if w["title"] == "Horoscope" and w["w"] > 200 and w["h"] > 200
    ]
    if not dialogs:
        dialogs = [w for w in wins if "Priorit" in w["title"] and w["w"] > 200]
    embeds = [w for w in wins if w["title"] == "Shell Embedding"]
    if not dialogs:
        return False

    dlg = dialogs[0]
    cw = max(100, dlg["w"] - 24)
    ch = max(100, dlg["h"] - 80)

    for i, emb in enumerate(embeds):
        if i == 0:
            xdo("windowsize", emb["id"], str(cw), str(ch))
            # place embed over dialog client area (absolute screen coords)
            xdo("windowmove", emb["id"], str(dlg["x"] + 8), str(dlg["y"] + 48))
            xdo("windowmap", emb["id"])
            xdo("windowraise", emb["id"])
        else:
            xdo("windowunmap", emb["id"])

    xdo("windowactivate", "--sync", dlg["id"])
    xdo("windowraise", dlg["id"])
    xdo("mousemove", "--window", dlg["id"], "220", "220")
    xdo("click", "1")
    xdo("key", "--window", dlg["id"], "F5")
    return True


def main() -> int:
    ok = refresh_once()
    print("refresh", "ok" if ok else "no-window")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
