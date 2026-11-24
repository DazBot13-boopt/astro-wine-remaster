#!/usr/bin/env python3
"""Lecteur Horoscope OREAC — UI soignée (remplace le TWebBrowser Wine blanc/noir).

Lit temp.rtf (Wine laisse souvent temp.htm vide). Masque les fenêtres Wine
blanches (Horoscope / Priorités / Shell Embedding) pour ne garder que ce lecteur.
"""
from __future__ import annotations

import html as htmlmod
import os
import re
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango, Gdk  # noqa: E402

ROOT = Path.home() / "Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope"
POLL_MS = 500
HIDE_WINE_MS = 1200

SIGN_LABELS = {
    "01_Belier": "Bélier",
    "01_Bélier": "Bélier",
    "02_Taureau": "Taureau",
    "03_Gemeaux": "Gémeaux",
    "03_Gémeaux": "Gémeaux",
    "04_Cancer": "Cancer",
    "05_Lion": "Lion",
    "06_Vierge": "Vierge",
    "07_Balance": "Balance",
    "08_Scorpion": "Scorpion",
    "09_Sagittaire": "Sagittaire",
    "10_Capricorne": "Capricorne",
    "11_Verseau": "Verseau",
    "12_Poissons": "Poissons",
}

ASPECT_RE = re.compile(
    r"(?im)^\s*(?:Le |La |L')?(?:Soleil|Lune|Mercure|V[eé]nus|Mars|Jupiter|Saturne|"
    r"Uranus|Neptune|Pluton|N[oe]ud)\b.{5,100}$"
)


def rtf_to_text(rtf: str) -> str:
    def hex_escape(m: re.Match) -> str:
        try:
            return bytes([int(m.group(1), 16)]).decode("cp1252", errors="replace")
        except Exception:
            return ""

    text = re.sub(r"\{\\fonttbl.*?\}", "", rtf, flags=re.S)
    text = re.sub(r"\{\\colortbl.*?\}", "", text, flags=re.S)
    text = re.sub(r"\{\\\*\\generator.*?\}", "", text, flags=re.S)
    text = re.sub(r"\\'([0-9a-fA-F]{2})", hex_escape, text)
    text = text.replace("\\par", "\n").replace("\\tab", "\t")
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    text = re.sub(
        r"(?im)^(System|Tahoma|Arial|Lucida Handwriting);?\s*$", "", text
    )
    # leftover single junk letters at line start from RTF bold markers
    text = re.sub(r"(?m)^[dDfF]\s+(?=[A-ZÀÂÄÉÈÊËÎÏÔÙÛÜ])", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_text(raw: bytes) -> str:
    raw = raw.replace(b"\x00", b"")
    m = re.search(br"charset=([a-zA-Z0-9_-]+)", raw, re.I)
    cs = (m.group(1).decode() if m else "cp1252").lower().replace(
        "windows-1252", "cp1252"
    )
    text = raw.decode("utf-8" if cs in ("utf-8", "utf8") else "cp1252", errors="replace")
    body = re.search(r"(?is)<body[^>]*>(.*)</body>", text)
    chunk = body.group(1) if body else text
    chunk = re.sub(r"(?is)<br\s*/?>", "\n", chunk)
    chunk = re.sub(r"(?is)</p\s*>", "\n\n", chunk)
    chunk = re.sub(r"(?is)<[^>]+>", "", chunk)
    return re.sub(r"\n{3,}", "\n\n", htmlmod.unescape(chunk)).strip()


def newest_pair() -> tuple[Path | None, Path | None]:
    best_m = 0.0
    best: tuple[Path | None, Path | None] = (None, None)
    for d in ROOT.glob("*/Res_Txt"):
        rtf, htm = d / "temp.rtf", d / "temp.htm"
        times = []
        if rtf.is_file():
            times.append(rtf.stat().st_mtime)
        if htm.is_file():
            times.append(htm.stat().st_mtime)
        if not times:
            continue
        m = max(times)
        if m >= best_m:
            best_m = m
            best = (rtf if rtf.is_file() else None, htm if htm.is_file() else None)
    return best


def load_text() -> tuple[str, str]:
    rtf, htm = newest_pair()
    label = "Horoscope"
    if rtf:
        label = rtf.parent.parent.name
        plain = rtf_to_text(rtf.read_text("latin-1", errors="replace"))
        if len(plain) >= 20:
            return label, plain
    if htm:
        label = htm.parent.parent.name
        plain = html_to_text(htm.read_bytes())
        if len(plain) >= 20:
            return label, plain
    return label, ""


def split_sections(plain: str) -> list[tuple[str, str]]:
    """Découpe en (titre, corps) pour une lecture claire."""
    lines = [ln.strip() for ln in plain.splitlines()]
    sections: list[tuple[str, str]] = []
    title: str | None = None
    body: list[str] = []

    def flush() -> None:
        nonlocal title, body
        if title is None and not body:
            return
        t = title or "Passage"
        sections.append((t, "\n\n".join(b for b in body if b).strip()))
        title, body = None, []

    for ln in lines:
        if not ln:
            continue
        if ASPECT_RE.match(ln):
            flush()
            title = ln
        else:
            body.append(ln)
    flush()
    if not sections and plain.strip():
        sections = [("Horoscope", plain.strip())]
    return sections


def hide_wine_blank_windows() -> None:
    """Masque les fenêtres Wine blanches / 1×1 (garde le menu principal)."""
    try:
        tree = subprocess.check_output(
            ["xwininfo", "-root", "-tree"], text=True, errors="replace"
        )
    except Exception:
        return
    for line in tree.splitlines():
        m = re.search(
            r"(0x[0-9a-f]+)\s+\"([^\"]*)\":\s+\(\"(horoscope_[^\"]+)\"",
            line,
            re.I,
        )
        if not m:
            continue
        wid, title = m.group(1), m.group(2)
        # garder éventuellement rien : tout le chrome Horoscope Wine est cassé
        if title in (
            "Horoscope",
            "Priorités du Mois",
            "Shell Embedding",
            "Default IME",
        ) or title.startswith("Horoscope "):
            subprocess.run(
                ["xdotool", "windowunmap", wid],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


CSS = b"""
window {
  background-color: #0a1012;
}
.header {
  background-color: #0c1214;
  padding: 18px 22px 14px 22px;
  border-bottom: 1px solid rgba(198, 161, 91, 0.35);
}
.brand {
  color: #c6a15b;
  font-size: 13px;
  letter-spacing: 4px;
  font-weight: 700;
}
.title {
  color: #f3ebdd;
  font-size: 34px;
  font-weight: 500;
  margin-top: 6px;
}
.subtitle {
  color: rgba(243, 235, 221, 0.62);
  font-size: 13px;
  margin-top: 4px;
}
.paper {
  background-color: #f3ebdd;
  color: #1a1510;
  border-radius: 0;
}
.paper text {
  background-color: #f3ebdd;
  color: #1a1510;
}
.scroll {
  background-color: #0a1012;
  padding: 18px 20px 28px 20px;
}
"""


class Viewer(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="OREAC — Horoscope")
        self.set_default_size(720, 820)
        self.set_position(Gtk.WindowPosition.CENTER)
        self._stamp = ""

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(outer)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header.get_style_context().add_class("header")
        self.lbl_brand = Gtk.Label(label="OREAC", xalign=0)
        self.lbl_brand.get_style_context().add_class("brand")
        self.lbl_title = Gtk.Label(label="Horoscope", xalign=0)
        self.lbl_title.get_style_context().add_class("title")
        self.lbl_sub = Gtk.Label(
            label="Lecture des transits · texte généré par l'application",
            xalign=0,
        )
        self.lbl_sub.get_style_context().add_class("subtitle")
        for w in (self.lbl_brand, self.lbl_title, self.lbl_sub):
            header.pack_start(w, False, False, 0)
        outer.pack_start(header, False, False, 0)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.get_style_context().add_class("scroll")
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.content.set_margin_top(8)
        self.content.set_margin_bottom(24)
        self.content.set_margin_start(4)
        self.content.set_margin_end(4)
        self.scroll.add(self.content)
        outer.pack_start(self.scroll, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        GLib.timeout_add(POLL_MS, self._tick)
        GLib.timeout_add(HIDE_WINE_MS, self._hide_wine)
        self._tick()

    def _hide_wine(self) -> bool:
        hide_wine_blank_windows()
        return True  # repeat

    def _clear_content(self) -> None:
        for child in list(self.content.get_children()):
            self.content.remove(child)

    def _add_section(self, title: str, body: str) -> None:
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        frame.get_style_context().add_class("paper")
        frame.set_margin_start(8)
        frame.set_margin_end(8)
        # inner padding via nested box
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        inner.set_margin_top(16)
        inner.set_margin_bottom(16)
        inner.set_margin_start(18)
        inner.set_margin_end(18)

        # accent line
        accent = Gtk.EventBox()
        accent.set_size_request(-1, 3)
        accent.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.78, 0.63, 0.36, 1)
        )

        h = Gtk.Label(label=title, xalign=0)
        h.set_line_wrap(True)
        h.override_font(Pango.FontDescription("Serif Bold 15"))
        h.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.12, 0.09, 0.06, 1))

        t = Gtk.Label(label=body, xalign=0, yalign=0)
        t.set_line_wrap(True)
        t.set_max_width_chars(62)
        t.override_font(Pango.FontDescription("Serif 12.5"))
        t.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.18, 0.14, 0.10, 1))

        # paper background on frame via eventbox
        paper = Gtk.EventBox()
        paper.override_background_color(
            Gtk.StateFlags.NORMAL, Gdk.RGBA(0.953, 0.922, 0.867, 1)
        )
        paper.add(inner)
        inner.pack_start(accent, False, False, 0)
        inner.pack_start(h, False, False, 0)
        inner.pack_start(t, False, False, 0)
        frame.pack_start(paper, True, True, 0)
        self.content.pack_start(frame, False, False, 0)

    def _tick(self) -> bool:
        rtf, htm = newest_pair()
        stamp = ""
        for p in (rtf, htm):
            if p and p.is_file():
                stamp += f"{p}:{p.stat().st_mtime};"
        if stamp == self._stamp and self._stamp:
            return True
        self._stamp = stamp

        folder, plain = load_text()
        pretty = SIGN_LABELS.get(folder, folder.replace("_", " "))
        self.lbl_title.set_text(pretty if pretty else "Horoscope")
        self.set_title(f"OREAC — Horoscope · {pretty}")

        self._clear_content()
        if not plain:
            empty = Gtk.Label(
                label="Choisis un signe dans le menu Wine.\nLe texte apparaîtra ici.",
                xalign=0.5,
            )
            empty.override_color(
                Gtk.StateFlags.NORMAL, Gdk.RGBA(0.95, 0.92, 0.87, 0.7)
            )
            empty.set_margin_top(40)
            self.content.pack_start(empty, False, False, 0)
        else:
            for title, body in split_sections(plain):
                if body or title:
                    self._add_section(title, body or "—")
        self.content.show_all()
        return True


def main() -> int:
    os.environ.setdefault("DISPLAY", ":0")
    # police serif si dispo
    win = Viewer()
    win.show_all()
    win.present()
    win.resize(720, 820)
    hide_wine_blank_windows()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
