#!/usr/bin/env python3
"""Curseur de défilement (trait tirable) superposé sur la fenêtre Portrait Wine.

Se place dans la bande droite (entre les pyramides ▲▼ Delphi) et envoie
molette / PageUp-PageDown à la fenêtre Astrologie.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

POLL_MS = 800


def sh(*args: str) -> str:
    try:
        return subprocess.check_output(args, text=True, errors="replace").strip()
    except Exception:
        return ""


def find_astro_window() -> dict | None:
    tree = sh("xwininfo", "-root", "-tree")
    best = None
    for line in tree.splitlines():
        # fenêtre contenu "Astrologie" (pas le launcher)
        m = re.search(
            r'(0x[0-9a-f]+)\s+"Astrologie":\s+\("astrologie\.exe"',
            line,
            re.I,
        )
        if not m:
            continue
        wh = re.search(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", line)
        if not wh:
            continue
        w, h, x, y = map(int, wh.groups())
        if w < 400 or h < 300:
            continue
        best = {"id": m.group(1), "w": w, "h": h, "x": x, "y": y}
    return best


def xdo(*args: str) -> None:
    subprocess.run(
        ["xdotool", *args],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class ScrollOverlay(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_app_paintable(True)
        self.set_default_size(22, 400)
        self._dragging = False
        self._last_y = 0
        self._astro: dict | None = None
        self._ratio = 0.0

        # fond semi-transparent + trait
        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            window {
              background-color: rgba(40, 20, 12, 0.25);
            }
            .rail {
              background-color: rgba(90, 40, 30, 0.35);
              border-radius: 8px;
            }
            .thumb {
              background-image: linear-gradient(180deg, #e07060, #8b281e 60%, #5a120e);
              border: 1px solid #3a0c08;
              border-radius: 8px;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.rail = Gtk.EventBox()
        self.rail.set_size_request(18, 400)
        self.rail.get_style_context().add_class("rail")
        self.rail.set_visible_window(True)

        self.fixed = Gtk.Fixed()
        self.rail.add(self.fixed)

        self.thumb = Gtk.EventBox()
        self.thumb.set_size_request(14, 48)
        self.thumb.get_style_context().add_class("thumb")
        self.thumb.set_visible_window(True)
        self.fixed.put(self.thumb, 2, 0)

        self.add(self.rail)

        self.thumb.connect("button-press-event", self._on_press)
        self.thumb.connect("button-release-event", self._on_release)
        self.thumb.connect("motion-notify-event", self._on_motion)
        self.thumb.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_HINT_MASK
        )
        self.rail.connect("button-press-event", self._on_rail_click)

        GLib.timeout_add(POLL_MS, self._reposition)
        self._reposition()

    def _on_press(self, _w, event) -> bool:
        if event.button == 1:
            self._dragging = True
            self._last_y = event.y_root
            return True
        return False

    def _on_release(self, _w, event) -> bool:
        if event.button == 1:
            self._dragging = False
            return True
        return False

    def _on_motion(self, _w, event) -> bool:
        if not self._dragging:
            return False
        dy = event.y_root - self._last_y
        self._last_y = event.y_root
        self._nudge_scroll(dy)
        self._move_thumb_by(dy)
        return True

    def _on_rail_click(self, _w, event) -> bool:
        if event.button != 1:
            return False
        # clic sur la rail → saut relatif
        alloc = self.rail.get_allocation()
        ratio = max(0.0, min(1.0, event.y / max(1, alloc.height)))
        delta = (ratio - self._ratio) * 800
        self._ratio = ratio
        self._nudge_scroll(delta)
        self._place_thumb_ratio(ratio)
        return True

    def _move_thumb_by(self, dy: float) -> None:
        alloc = self.rail.get_allocation()
        th = 48
        max_top = max(0, alloc.height - th)
        # current
        children = self.fixed.get_children()
        # GtkFixed doesn't expose child y easily; track ratio
        self._ratio = max(0.0, min(1.0, self._ratio + dy / max(1, max_top)))
        self._place_thumb_ratio(self._ratio)

    def _place_thumb_ratio(self, ratio: float) -> None:
        alloc = self.rail.get_allocation()
        th = 48
        max_top = max(0, alloc.height - th)
        y = int(ratio * max_top)
        self.fixed.move(self.thumb, 2, y)

    def _nudge_scroll(self, dy: float) -> None:
        """dy>0 = vers le bas du document."""
        if not self._astro:
            return
        wid = str(int(self._astro["id"], 16))
        xdo("windowactivate", "--sync", wid)
        # clic dans la zone contenu (évite les boutons FERMER/SOMMAIRE)
        cx = max(80, self._astro["w"] // 2)
        cy = max(120, self._astro["h"] // 2)
        xdo("mousemove", "--window", wid, str(cx), str(cy))
        steps = int(abs(dy) / 12) + 1
        btn = "5" if dy > 0 else "4"  # 5=wheel down, 4=wheel up
        for _ in range(min(steps, 12)):
            xdo("click", "--window", wid, btn)

    def _reposition(self) -> bool:
        astro = find_astro_window()
        if not astro:
            self.hide()
            self._astro = None
            return True
        self._astro = astro
        # bande droite parchemin ~ entre pyramides : ~18-28px from right, below header
        overlay_w = 22
        margin_right = 10
        top = astro["y"] + 70
        height = max(200, astro["h"] - 100)
        left = astro["x"] + astro["w"] - overlay_w - margin_right
        self.resize(overlay_w, height)
        self.move(left, top)
        self.rail.set_size_request(overlay_w - 4, height - 4)
        if not self.get_visible():
            self.show_all()
            self._place_thumb_ratio(self._ratio)
        return True


def main() -> int:
    os.environ.setdefault("DISPLAY", ":0")
    # un seul overlay
    win = ScrollOverlay()
    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
