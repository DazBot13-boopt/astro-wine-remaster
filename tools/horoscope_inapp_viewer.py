#!/usr/bin/env python3
"""Lecteur Horoscope intégré (GTK/WebKit) — remplace le TWebBrowser Wine cassé.

Ce n'est PAS Firefox/Chrome : fenêtre dédiée du remaster, style app d'origine.
Se met à jour dès que Res_Txt/temp.htm change.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, WebKit2, GLib  # noqa: E402

ROOT = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
POLL_MS = 800


def newest_htm() -> Path | None:
    cands = list(ROOT.glob("*/Res_Txt/temp.htm"))
    if not cands:
        return None
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0]


def load_html(path: Path) -> tuple[str, str]:
    raw = path.read_bytes().replace(b"\x00", b"")
    m = re.search(br"charset=([a-zA-Z0-9_-]+)", raw, re.I)
    cs = (m.group(1).decode() if m else "cp1252").lower().replace("windows-1252", "cp1252")
    if cs in ("utf-8", "utf8"):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = raw.decode("cp1252", errors="replace")
    # force readable in WebKit
    text = re.sub(
        r'(?i)<meta[^>]+charset=[^>]+>',
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
        text,
        count=1,
    )
    if "charset=utf-8" not in text.lower():
        text = text.replace("<HEAD>", '<HEAD><meta charset="utf-8">', 1)
        text = text.replace("<head>", '<head><meta charset="utf-8">', 1)
    base = path.parent.as_uri() + "/"
    return text, base


class Viewer(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Horoscope — OREAC")
        self.set_default_size(820, 640)
        self.set_border_width(0)
        self._mtime = 0.0
        self._path: Path | None = None

        self.view = WebKit2.WebView()
        settings = self.view.get_settings()
        settings.set_enable_javascript(True)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.view)
        self.add(scroll)
        self.connect("destroy", Gtk.main_quit)

        # fond bleu d'origine pendant chargement
        css = Gtk.CssProvider()
        css.load_from_data(b"window { background-color: #0E3A6E; }")
        self.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        GLib.timeout_add(POLL_MS, self._tick)
        self._tick()

    def _tick(self) -> bool:
        p = newest_htm()
        if not p:
            return True
        try:
            mt = p.stat().st_mtime
        except OSError:
            return True
        if p == self._path and mt <= self._mtime:
            return True
        self._path = p
        self._mtime = mt
        try:
            html, base = load_html(p)
            sign = p.parent.parent.name
            self.set_title(f"Horoscope — {sign}")
            self.view.load_html(html, base)
        except Exception as e:
            self.view.load_html(f"<pre>Erreur lecture: {e}</pre>", "file:///")
        return True


def main() -> int:
    os.environ.setdefault("DISPLAY", ":0")
    win = Viewer()
    win.show_all()
    # amener au premier plan
    win.present()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
