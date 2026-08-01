"""ENDLESS LOOP x4 — the 2x2 lane mosaic (punch-list #24-x4).

Pure PIL, deliberately free of Tk and of `context`, so the tile view can be rendered
and eyeballed without a running emulator or a window:

    from modules.tile_mosaic import MosaicTile, compose_mosaic
    compose_mosaic((960, 640), tiles, focus=0).save("preview.png")

The dashboard (`DashboardScreen._update_x4_tiles`) reads shared memory, builds the
`MosaicTile` list and hands it here; everything about how the grid LOOKS lives in this
file.

‼ WHY IT COMPOSES AT FINAL SIZE
-------------------------------
The obvious implementation builds a 480x320 mosaic and lets the canvas upscale it, the
way `_update_video` does for a single screen. That makes the labels an unreadable blur,
because the upscale is NEAREST (correct for GBA pixels, ruinous for text). So the game
frames are upscaled NEAREST into their cells and the text is drawn afterwards at the
final resolution, where it stays crisp.
"""

from __future__ import annotations

from dataclasses import dataclass

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

#: Cell background for a lane that has not published a frame yet.
_EMPTY_CELL = (14, 14, 16)
_TEXT = (255, 255, 255)
_SUBTEXT = (190, 200, 210)
_DEAD_TEXT = (255, 120, 120)

_font_cache: dict[int, object] = {}


@dataclass
class MosaicTile:
    """Everything the grid needs to know about one lane."""

    tag: str = "P?"
    starter: str = ""
    #: What the lane is ACTUALLY playing this run. For a `random` lane this differs from
    #: `starter` and the label shows both ("random -> Treecko"), so a random lane that
    #: rolled the same species as a pinned lane can no longer be mistaken for a duplicate
    #: of it (user report 2026-07-26).
    starter_chosen: str | None = None
    alive: bool = True
    exhausted: bool = False        # died and used up its restart budget
    restarts: int = 0
    runs_completed: int = 0
    message: str = ""
    party: str = ""
    #: Debug-log state, so "is this lane actually producing logs?" is answerable from the
    #: grid instead of by hunting the filesystem (user, 2026-07-26: the logs were being
    #: written all along, in the lane profile the user had not thought to look in).
    #: None = the lane has not reported a log; the tile then says so loudly.
    log_bytes: int | None = None
    #: Raw RGB888 screen, or None if the lane has not published yet.
    pixels: bytes | None = None
    width: int = 240
    height: int = 160


def _font(size: int):
    if size not in _font_cache:
        try:
            _font_cache[size] = PIL.ImageFont.truetype("segoeui.ttf", size)
        except Exception:
            try:
                _font_cache[size] = PIL.ImageFont.load_default(size)
            except Exception:
                _font_cache[size] = PIL.ImageFont.load_default()
    return _font_cache[size]


def _kb(size: int) -> str:
    """Compact byte count for the tile label."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _fit(draw, text: str, font, max_width: int) -> str:
    """Truncate `text` with an ellipsis so it fits `max_width` pixels."""
    if not text:
        return ""
    try:
        if draw.textlength(text, font=font) <= max_width:
            return text
        while text and draw.textlength(text + "…", font=font) > max_width:
            text = text[:-1]
        return text + "…"
    except Exception:
        return text[:40]


def compose_mosaic(size: tuple[int, int], tiles: list[MosaicTile], focus: int = 0,
                   accent: str = "#3987e5") -> PIL.Image.Image:
    """Render the 2x2 grid at `size` pixels. Always returns an image; never raises."""
    cell_w = max(120, size[0] // 2)
    cell_h = max(80, size[1] // 2)
    mosaic = PIL.Image.new("RGB", (cell_w * 2, cell_h * 2), (0, 0, 0))
    draw = PIL.ImageDraw.Draw(mosaic, "RGBA")

    head_font = _font(max(11, cell_h // 20))
    detail_font = _font(max(10, cell_h // 24))
    pad = max(4, cell_h // 40)
    head_h = int(getattr(head_font, "size", 14) * 1.15)
    detail_h = int(getattr(detail_font, "size", 12) * 1.15)
    bar_h = pad * 2 + head_h + detail_h

    for slot in range(4):
        tile = tiles[slot] if slot < len(tiles) else MosaicTile(tag=f"P{slot + 1}")
        ox, oy = (slot % 2) * cell_w, (slot // 2) * cell_h

        if tile.pixels and len(tile.pixels) == tile.width * tile.height * 3:
            screen = PIL.Image.frombytes("RGB", (tile.width, tile.height), tile.pixels)
            mosaic.paste(screen.resize((cell_w, cell_h), resample=PIL.Image.NEAREST), (ox, oy))
        else:
            draw.rectangle([ox, oy, ox + cell_w - 1, oy + cell_h - 1], fill=_EMPTY_CELL)
            draw.text((ox + cell_w // 2, oy + cell_h // 2), "waiting for the lane to boot…",
                      font=detail_font, fill=(150, 150, 150), anchor="mm")

        # A dead lane must be obvious at a glance, not inferred from a frozen frame.
        if not tile.alive:
            draw.rectangle([ox, oy, ox + cell_w - 1, oy + cell_h - 1], fill=(0, 0, 0, 150))
            draw.text((ox + cell_w // 2, oy + cell_h // 2),
                      "STOPPED" if tile.exhausted else "restarting…",
                      font=head_font, fill=_DEAD_TEXT, anchor="mm")

        draw.rectangle([ox, oy + cell_h - bar_h, ox + cell_w - 1, oy + cell_h - 1], fill=(0, 0, 0, 175))

        runs = tile.runs_completed
        starter = tile.starter
        if tile.starter_chosen and tile.starter_chosen.lower() != (tile.starter or "").lower():
            starter = f"{tile.starter}→{tile.starter_chosen}"
        head = f"{tile.tag} · {starter} · {runs} run{'' if runs == 1 else 's'} done"
        if tile.restarts:
            head += f" · {tile.restarts} restart{'' if tile.restarts == 1 else 's'}"
        head += f" · log {_kb(tile.log_bytes)}" if tile.log_bytes is not None else " · ‼ NO LOG"
        draw.text((ox + pad, oy + cell_h - bar_h + pad),
                  _fit(draw, head, head_font, cell_w - pad * 2), font=head_font,
                  fill=_TEXT if tile.log_bytes is not None else _DEAD_TEXT)

        detail = tile.message or ""
        if tile.party:
            detail = f"{tile.party}   |   {detail}" if detail else tile.party
        draw.text((ox + pad, oy + cell_h - bar_h + pad + head_h),
                  _fit(draw, detail, detail_font, cell_w - pad * 2), font=detail_font, fill=_SUBTEXT)

        if slot == focus:
            draw.rectangle([ox + 1, oy + 1, ox + cell_w - 2, oy + cell_h - 2], outline=accent, width=3)

    return mosaic
