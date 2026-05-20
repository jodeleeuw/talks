#!/usr/bin/env python3
"""
pptx-to-slidev prep: scaffold a Slidev talk dir from a PPTX file and
emit a structured analysis Claude can read to write slides.md.

Stdlib only. Writes a new talk dir under <repo>/<output-name>/ containing:
  - everything in template/ (package.json, slides.md, vite.config.ts,
    components/Diagram.vue, diagrams/, ...)
  - every image from the PPTX, co-located with slides.md
  - _analysis.json + _analysis.md describing each slide
"""

import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EMU_PER_PX = 9525
DEFAULT_DECK = (960, 540)


def emu_to_px(v):
    try:
        return round(int(v) / EMU_PER_PX, 1)
    except Exception:
        return None


def slugify(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
    return re.sub(r"^-+|-+$", "", s)


def parse_xml(zf, path):
    try:
        with zf.open(path) as f:
            return ET.parse(f).getroot()
    except KeyError:
        return None


def get_deck_size(root):
    if root is None:
        return DEFAULT_DECK
    sld_sz = root.find("p:sldSz", NS)
    if sld_sz is None:
        return DEFAULT_DECK
    cx = emu_to_px(sld_sz.attrib.get("cx", 0))
    cy = emu_to_px(sld_sz.attrib.get("cy", 0))
    return (cx or DEFAULT_DECK[0], cy or DEFAULT_DECK[1])


def _group_transform(grpSp):
    """Return (dx, dy, sx, sy) for a p:grpSp's child coordinate system.

    A group's xfrm carries both the group's slide-position (off/ext) and its
    internal coordinate system (chOff/chExt). A child at (cx, cy) in the group's
    local frame renders at slide coord (off.x + (cx - chOff.x) * (ext / chExt),
    off.y + (cy - chOff.y) * (ext / chExt)). Returns the (dx, dy, sx, sy) that
    maps local → slide.
    """
    xfrm = grpSp.find("p:grpSpPr/a:xfrm", NS)
    if xfrm is None:
        return (0.0, 0.0, 1.0, 1.0)
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    chOff = xfrm.find("a:chOff", NS)
    chExt = xfrm.find("a:chExt", NS)
    if off is None or ext is None or chOff is None or chExt is None:
        return (0.0, 0.0, 1.0, 1.0)
    ox = emu_to_px(off.attrib.get("x", 0))
    oy = emu_to_px(off.attrib.get("y", 0))
    ex = emu_to_px(ext.attrib.get("cx", 0))
    ey = emu_to_px(ext.attrib.get("cy", 0))
    cox = emu_to_px(chOff.attrib.get("x", 0))
    coy = emu_to_px(chOff.attrib.get("y", 0))
    cex = emu_to_px(chExt.attrib.get("cx", 0))
    cey = emu_to_px(chExt.attrib.get("cy", 0))
    sx = ex / cex if cex else 1.0
    sy = ey / cey if cey else 1.0
    return (ox - cox * sx, oy - coy * sy, sx, sy)


def _compose_transform(outer, inner):
    """Compose two (dx, dy, sx, sy) transforms — outer applied to inner's output."""
    odx, ody, osx, osy = outer
    idx, idy, isx, isy = inner
    return (odx + osx * idx, ody + osy * idy, osx * isx, osy * isy)


def _walk_shapes(root):
    """Yield (element, transform) for each sp / cxnSp / pic / graphicFrame,
    applying any enclosing p:grpSp transforms so element bboxes can be mapped
    to slide-absolute coords. `graphicFrame` covers tables (and charts, though
    those aren't surfaced here)."""
    def walk(parent, transform):
        for child in parent:
            tag = child.tag.split('}', 1)[-1]
            if tag == 'grpSp':
                new_t = _compose_transform(transform, _group_transform(child))
                yield from walk(child, new_t)
            elif tag in ('sp', 'cxnSp', 'pic', 'graphicFrame'):
                yield child, transform
            else:
                yield from walk(child, transform)
    yield from walk(root, (0.0, 0.0, 1.0, 1.0))


def apply_transform(bbox, transform):
    """Apply (dx, dy, sx, sy) to a bbox dict; returns a new dict (or None)."""
    if bbox is None:
        return None
    dx, dy, sx, sy = transform
    return {
        **bbox,
        "x": dx + sx * bbox["x"],
        "y": dy + sy * bbox["y"],
        "w": sx * bbox["w"],
        "h": sy * bbox["h"],
    }


def get_xfrm(elem):
    # `<p:graphicFrame>` (tables, charts) stores its xfrm directly under the
    # element — no `spPr` / `grpSpPr` wrapper.
    xfrm = elem.find("p:spPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = elem.find("p:grpSpPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = elem.find("p:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return None
    return {
        "x": emu_to_px(off.attrib.get("x", 0)),
        "y": emu_to_px(off.attrib.get("y", 0)),
        "w": emu_to_px(ext.attrib.get("cx", 0)),
        "h": emu_to_px(ext.attrib.get("cy", 0)),
        "flipH": xfrm.attrib.get("flipH") == "1",
        "flipV": xfrm.attrib.get("flipV") == "1",
    }


_VERT_MAP = {
    # `vert` / `eaVert` rotate text 90° counter-clockwise (reads bottom-to-top
    # on the right edge). `vert270` rotates clockwise (reads top-to-bottom on
    # the left edge). `wordArtVert` stacks individual letters top-to-bottom
    # without rotating them.
    "vert": 270,
    "eaVert": 270,
    "vert270": 90,
    "mongolianVert": 90,
    "wordArtVert": "stacked",
    "wordArtVertRtl": "stacked",
}


def _text_rotation(elem):
    """Return a normalized vertical-text annotation for a shape, or None.

    Considers two independent PPTX mechanisms:
      - `<a:bodyPr vert="...">` — the text frame's own writing direction.
      - `<p:spPr><a:xfrm rot="...">` — the whole shape (and its text) is rotated
        in slide space. The PPTX `rot` attribute is in 60000ths of a degree.

    Returns one of:
      - an integer rotation in degrees (positive = clockwise), normalized into
        `[1, 359]` so horizontal text is never reported.
      - the string `"stacked"` for `wordArtVert*` body orientation.
      - None when the text reads left-to-right horizontally.
    """
    if elem is None:
        return None
    body = elem.find("p:txBody/a:bodyPr", NS)
    if body is not None:
        vert = body.attrib.get("vert")
        if vert and vert in _VERT_MAP:
            return _VERT_MAP[vert]
    xfrm = elem.find("p:spPr/a:xfrm", NS)
    if xfrm is not None:
        rot_raw = xfrm.attrib.get("rot")
        if rot_raw:
            try:
                deg = int(rot_raw) / 60000.0
            except (TypeError, ValueError):
                deg = 0.0
            # Normalize into [0, 360); skip near-horizontal.
            deg = deg % 360
            if 1 <= round(deg) <= 359:
                return round(deg)
    return None


def _fill_color(spPr):
    """Return the shape's explicit sRGB fill as '#RRGGBB', or None.

    Only picks up `<a:solidFill><a:srgbClr val="..."/></a:solidFill>`. Theme
    color references (`<a:schemeClr>`) are deliberately skipped — those default
    to white/dark and would clobber the theme's `--slidev-theme-bg`. We only
    want fills the author chose explicitly (e.g. grayscale activity encoding).
    """
    if spPr is None:
        return None
    sf = spPr.find("a:solidFill", NS)
    if sf is None:
        return None
    srgb = sf.find("a:srgbClr", NS)
    if srgb is None:
        return None
    val = srgb.attrib.get("val")
    return f"#{val}" if val else None


def _relative_luminance(hex_color):
    """sRGB relative luminance per WCAG: 0 = black, 1 = white. None if unparseable."""
    if not hex_color:
        return None
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return None
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return None
    def chan(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def _is_full_slide_overlay(bbox, fill, deck_size, edge_tol=2.0):
    """True if a shape is a low-luminance rect covering the whole deck.

    Used to spot "darken-the-photo" scrims authors stack between a background
    picture and foreground text. `edge_tol` lets us tolerate the sub-pixel
    drift that PPTX export produces (e.g. an off=`-150` EMU = `-0.02 px`).
    """
    if not bbox or not fill:
        return False
    deck_w, deck_h = deck_size
    if (
        bbox.get("x") is None or bbox.get("y") is None
        or bbox.get("w") is None or bbox.get("h") is None
    ):
        return False
    if abs(bbox["x"]) > edge_tol or abs(bbox["y"]) > edge_tol:
        return False
    if abs(bbox["w"] - deck_w) > edge_tol or abs(bbox["h"] - deck_h) > edge_tol:
        return False
    lum = _relative_luminance(fill)
    if lum is None:
        return False
    return lum < 0.3


def _parse_table(frame, tbl, transform):
    """Extract a PPTX `<a:tbl>` into a structured record.

    Returns `{bbox, cols, rows, headers, body}` where `headers` is either a
    list of cell-text strings (one per column) or None when no header row was
    detected, and `body` is a list of rows, each a list of cell-text strings.

    Header detection: first row's `<a:tr h="1">` attribute is the authoritative
    signal; failing that, we treat the row as headers when every non-empty cell
    in it has bold-styled text. Authoring decks sometimes leave both signals
    off, so the fallback to `headers: None` is intentional.
    """
    bbox = apply_transform(get_xfrm(frame), transform)
    grid = tbl.find("a:tblGrid", NS)
    cols = len(grid.findall("a:gridCol", NS)) if grid is not None else 0

    tblPr = tbl.find("a:tblPr", NS)
    first_row_flag = tblPr is not None and tblPr.attrib.get("firstRow") == "1"

    rows_raw = []
    for tr in tbl.findall("a:tr", NS):
        row_h = tr.attrib.get("h", "")
        cells = []
        for tc in tr.findall("a:tc", NS):
            paragraphs = extract_paragraphs(tc)
            cell_text = "\n".join(p["text"] for p in paragraphs).strip()
            all_bold = bool(paragraphs) and all(
                all(r.get("bold") for r in p.get("runs", []) if r.get("text", "").strip())
                for p in paragraphs
                if any(r.get("text", "").strip() for r in p.get("runs", []))
            )
            cells.append({"text": cell_text, "bold": all_bold})
        rows_raw.append({"h": row_h, "cells": cells})

    headers = None
    body_rows = [r["cells"] for r in rows_raw]
    if rows_raw:
        first = rows_raw[0]
        first_texts = [c["text"] for c in first["cells"]]
        # OOXML signals: `<a:tblPr firstRow="1">` is the canonical "this table
        # has a header row" marker; a literal `<a:tr h="1">` row-attribute also
        # appears in some authoring tools. Failing both, fall back to the
        # heuristic "every non-empty cell in row 1 is bold".
        h1 = first.get("h") == "1"
        any_text = any(t.strip() for t in first_texts)
        all_bold_with_text = any_text and all(
            c["bold"] for c in first["cells"] if c["text"].strip()
        )
        if first_row_flag or h1 or all_bold_with_text:
            headers = first_texts
            body_rows = body_rows[1:]

    rows = [[c["text"] for c in row] for row in body_rows]
    if not cols and rows:
        cols = max(len(r) for r in rows)
    if not cols and headers:
        cols = len(headers)

    return {
        "bbox": bbox,
        "cols": cols,
        "rows": len(rows),
        "headers": headers,
        "body": rows,
    }


def _run_format(r):
    """Extract bold/italic/strike/underline/color from a run's rPr.

    None color = inherits default. `strike` is True for any non-`noStrike`
    value (PPTX uses `sngStrike` / `dblStrike`). `underline` is True for any
    non-`none` u= value (`sng`, `dbl`, `heavy`, …).
    """
    rpr = r.find("a:rPr", NS)
    bold = italic = strike = underline = False
    color = None
    if rpr is not None:
        bold = rpr.attrib.get("b") == "1"
        italic = rpr.attrib.get("i") == "1"
        sv = rpr.attrib.get("strike")
        if sv and sv != "noStrike":
            strike = True
        uv = rpr.attrib.get("u")
        if uv and uv != "none":
            underline = True
        clr = rpr.find(".//a:srgbClr", NS)
        if clr is not None:
            color = clr.attrib.get("val")
    return bold, italic, strike, underline, color


def extract_paragraphs(elem):
    """Return [{text, level, runs}] for each non-empty paragraph under elem.

    Each run is {text, bold, italic, color} where color is the 6-char srgb hex
    or None (inherits default). Runs let downstream code spot highlight builds
    where adjacent slides share text but differ in per-run formatting.
    """
    a_ns = "{%s}" % NS["a"]
    out = []
    for p in elem.iter(a_ns + "p"):
        runs = []
        for child in list(p):
            tag = child.tag[len(a_ns):] if child.tag.startswith(a_ns) else child.tag
            if tag == "r":
                bold, italic, strike, underline, color = _run_format(child)
                t = child.find("a:t", NS)
                text = (t.text or "") if t is not None else ""
                runs.append({
                    "text": text, "bold": bold, "italic": italic,
                    "strike": strike, "underline": underline, "color": color,
                })
            elif tag == "fld":
                t = child.find("a:t", NS)
                text = (t.text or "") if t is not None else ""
                runs.append({
                    "text": text, "bold": False, "italic": False,
                    "strike": False, "underline": False, "color": None,
                })
            elif tag == "br":
                runs.append({
                    "text": "\n", "bold": False, "italic": False,
                    "strike": False, "underline": False, "color": None,
                })
        full = "".join(r["text"] for r in runs)
        if not full.strip():
            continue
        level = 0
        pPr = p.find("a:pPr", NS)
        if pPr is not None and pPr.attrib.get("lvl"):
            try:
                level = int(pPr.attrib["lvl"])
            except ValueError:
                pass
        out.append({"text": full, "level": level, "runs": runs})
    return out


def _parse_src_rect(pic):
    """Read `<a:srcRect>` from a `<p:pic>` and return crop info, or None.

    PPTX expresses crops as four edge insets (`l`/`t`/`r`/`b`) in 1/1000ths of
    a percent of the source image's natural width/height. Missing attribute = 0.
    The visible portion of the source is then stretched to fill the picture's
    bbox — so to reproduce it in HTML we need to scale the `<img>` up and shift
    it inside an `overflow:hidden` wrapper that matches the bbox.

    Returns a dict with both the raw percentages and a set of precomputed CSS
    values (as percentages of the wrapper) so callers can drop them straight
    into a style block. Returns None when there's no crop (all edges = 0).
    """
    sr = pic.find("p:blipFill/a:srcRect", NS)
    if sr is None:
        return None

    def pct(attr):
        v = sr.attrib.get(attr, "0")
        try:
            return round(int(v) / 1000, 3)  # PPTX 1000ths-of-a-percent → percent
        except (TypeError, ValueError):
            return 0.0

    l, t, r, b = pct("l"), pct("t"), pct("r"), pct("b")
    if l == 0 and t == 0 and r == 0 and b == 0:
        return None

    # Visible portion of the source image, as a fraction of the source.
    visible_w = 100 - l - r
    visible_h = 100 - t - b
    if visible_w <= 0 or visible_h <= 0:
        return None  # malformed crop — fall back to uncropped

    # CSS values: with the wrapper sized to the bbox and overflow:hidden,
    # the <img> needs to be scaled up so the visible portion of the source
    # fills the wrapper, then shifted left/up so the visible portion starts at (0,0).
    return {
        "l": l, "t": t, "r": r, "b": b,
        "img_width_pct":  round(10000 / visible_w, 2),   # >= 100
        "img_height_pct": round(10000 / visible_h, 2),
        "img_left_pct":   round(-100 * l / visible_w, 2),  # <= 0
        "img_top_pct":    round(-100 * t / visible_h, 2),
    }


def parse_rels(zf, rels_path):
    """Return {rId: target_basename} for image rels."""
    root = parse_xml(zf, rels_path)
    if root is None:
        return {}
    out = {}
    for rel in root:
        rid = rel.attrib.get("Id", "")
        target = rel.attrib.get("Target", "")
        if "image" in target.lower():
            out[rid] = os.path.basename(target)
    return out


# PPTX connection-site indices for common preset shapes. The 4 cardinal sites
# (top/left/bottom/right) cover rect, roundRect, ellipse, and diamond — which
# are essentially every shape used in talk diagrams.
#
# Google Slides' PPTX export uses a counter-clockwise ordering: 0=top, 1=left,
# 2=bottom, 3=right. The OOXML spec defines the preset shapes with clockwise
# ordering (top/right/bottom/left), but Google's export ignores that and emits
# its own indices. Since this skill is aimed at Google-Slides decks, we follow
# Google's convention. Verified empirically against connector bbox geometry on
# the "01 - What is a model" deck — every idx=1 lined up with the left edge,
# every idx=3 with the right.
_SITE_NAMES = ["top", "left", "bottom", "right"]


def _local_site(prst, w, h, idx):
    """Return (lx, ly, name) in shape-local coords, or None if idx is unknown.

    Falls back to the 4-cardinal convention for unknown presets — wrong for
    chevrons/triangles, but those don't appear in talk diagrams in practice.
    """
    if idx is None or w is None or h is None:
        return None
    if not (0 <= idx < 4):
        return None
    sites = [
        (w / 2, 0),       # 0: top
        (0, h / 2),       # 1: left
        (w / 2, h),       # 2: bottom
        (w, h / 2),       # 3: right
    ]
    lx, ly = sites[idx]
    return (round(lx, 1), round(ly, 1), _SITE_NAMES[idx])


def _shape_snap_point(shape, idx):
    """Return {x, y, shape_id, site} for a snap onto a shape's connection site."""
    bb = shape.get("bbox") or {}
    if bb.get("x") is None:
        return None
    site = _local_site(shape.get("prst", ""), bb.get("w"), bb.get("h"), idx)
    if site is None:
        return None
    lx, ly, name = site
    return {
        "x": round(bb["x"] + lx, 1),
        "y": round(bb["y"] + ly, 1),
        "shape_id": shape.get("id"),
        "site": name,
    }


def _bbox_endpoints(bbox):
    """Best-effort (start, end) for an unsnapped connector from its bbox + flips.

    Connectors run diagonally across their bbox; flipH/flipV swap the corners.
    Rotation is ignored — the unsnapped case is approximate by definition.
    """
    if not bbox or bbox.get("x") is None:
        return None, None
    x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
    sx, sy = x, y
    ex, ey = x + w, y + h
    if bbox.get("flipH"):
        sx, ex = ex, sx
    if bbox.get("flipV"):
        sy, ey = ey, sy
    return (
        {"x": round(sx, 1), "y": round(sy, 1), "shape_id": None, "site": None},
        {"x": round(ex, 1), "y": round(ey, 1), "shape_id": None, "site": None},
    )


def _classify_kind(prst):
    """Map a connector preset name to a coarse routing kind."""
    if not prst:
        return "unknown"
    if prst.startswith("straight"):
        return "straight"
    if prst.startswith("bentConnector"):
        # bentConnector2 = one bend (L), bentConnector3 = two bends (U/Z), etc.
        suffix = prst[len("bentConnector"):]
        return f"bent{suffix}" if suffix.isdigit() else "bent"
    if prst.startswith("curved"):
        return "curved"
    return prst


_SIDE_NORMAL = {
    "top":    (0, -1),
    "right":  (1,  0),
    "bottom": (0,  1),
    "left":   (-1, 0),
}


def _bent4_path(sx, sy, ex, ey, s_site, e_site, off, fmt):
    """3-bend path: perpendicular leave, corner, perpendicular arrive.

    Matches PowerPoint's bentConnector4 routing (and is the right shape for
    same-shape "self-loop" connectors on adjacent sides — the perpendicular
    stubs naturally wrap around the shape's corner).
    """
    s_known = s_site in _SIDE_NORMAL
    e_known = e_site in _SIDE_NORMAL
    if not s_known and not e_known:
        return f"M {fmt(sx)} {fmt(sy)} L {fmt(ex)} {fmt(ey)}"

    # Partial info: one end free, the other snapped — emit a 1-bend path that
    # arrives perpendicular at the known end. Better than a diagonal, but
    # without the free end's exit direction we can't draw the full 3-bend wrap.
    if s_known and not e_known:
        snx, sny = _SIDE_NORMAL[s_site]
        s_stub = (sx + snx * off, sy + sny * off)
        return f"M {fmt(sx)} {fmt(sy)} L {fmt(s_stub[0])} {fmt(s_stub[1])} L {fmt(ex)} {fmt(ey)}"
    if e_known and not s_known:
        enx, eny = _SIDE_NORMAL[e_site]
        e_stub = (ex + enx * off, ey + eny * off)
        return f"M {fmt(sx)} {fmt(sy)} L {fmt(e_stub[0])} {fmt(e_stub[1])} L {fmt(ex)} {fmt(ey)}"

    snx, sny = _SIDE_NORMAL[s_site]
    enx, eny = _SIDE_NORMAL[e_site]
    s_stub = (sx + snx * off, sy + sny * off)
    e_stub = (ex + enx * off, ey + eny * off)
    s_horiz = s_site in ("left", "right")
    e_horiz = e_site in ("left", "right")
    if s_horiz != e_horiz:
        # Adjacent sides — single L-bend between the two stubs.
        corner_x = s_stub[0] if s_horiz else e_stub[0]
        corner_y = e_stub[1] if s_horiz else s_stub[1]
        return (
            f"M {fmt(sx)} {fmt(sy)} "
            f"L {fmt(s_stub[0])} {fmt(s_stub[1])} "
            f"L {fmt(corner_x)} {fmt(corner_y)} "
            f"L {fmt(e_stub[0])} {fmt(e_stub[1])} "
            f"L {fmt(ex)} {fmt(ey)}"
        )
    # Parallel sides — Z-bend through the midpoint between the stubs.
    if s_horiz:
        mid_x = (s_stub[0] + e_stub[0]) / 2
        return (
            f"M {fmt(sx)} {fmt(sy)} "
            f"L {fmt(s_stub[0])} {fmt(s_stub[1])} "
            f"L {fmt(mid_x)} {fmt(s_stub[1])} "
            f"L {fmt(mid_x)} {fmt(e_stub[1])} "
            f"L {fmt(e_stub[0])} {fmt(e_stub[1])} "
            f"L {fmt(ex)} {fmt(ey)}"
        )
    mid_y = (s_stub[1] + e_stub[1]) / 2
    return (
        f"M {fmt(sx)} {fmt(sy)} "
        f"L {fmt(s_stub[0])} {fmt(s_stub[1])} "
        f"L {fmt(s_stub[0])} {fmt(mid_y)} "
        f"L {fmt(e_stub[0])} {fmt(mid_y)} "
        f"L {fmt(e_stub[0])} {fmt(e_stub[1])} "
        f"L {fmt(ex)} {fmt(ey)}"
    )


def _suggest_path(connector, bend_offset=30):
    """Synthesize an SVG `d` string that matches the source routing kind.

    Straight connectors → `L`. Bent connectors → orthogonal `H`/`V` segments
    (sharp 90° corners, like PowerPoint draws them). Curved connectors → a
    quadratic Bézier through the midpoint, EXCEPT for self-loops which use the
    same 3-bend wrap as bent4. Returns None when endpoints are unknown.
    """
    st = connector.get("start") or {}
    en = connector.get("end") or {}
    sx, sy, ex, ey = st.get("x"), st.get("y"), en.get("x"), en.get("y")
    if None in (sx, sy, ex, ey):
        return None

    kind = connector.get("kind", _classify_kind(connector.get("prst", "")))
    s_site = st.get("site")
    e_site = en.get("site")
    s_id = st.get("shape_id")
    e_id = en.get("shape_id")
    self_loop = bool(s_id and s_id == e_id)

    def fmt(n):
        # Trim trailing .0 for readability.
        return f"{n:g}"

    # Self-loops always need a wrap path — the diagonal between two sites on
    # the same shape goes through the shape's interior, which is nonsense.
    if self_loop and s_site and e_site:
        return _bent4_path(sx, sy, ex, ey, s_site, e_site, bend_offset, fmt)

    if kind == "straight":
        return f"M {fmt(sx)} {fmt(sy)} L {fmt(ex)} {fmt(ey)}"

    if kind == "curved":
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        return f"M {fmt(sx)} {fmt(sy)} Q {fmt(mx)} {fmt(my)} {fmt(ex)} {fmt(ey)}"

    if kind == "bent2":
        # L-bend: leave the start perpendicular to its site, then turn 90°.
        if s_site in ("top", "bottom"):
            return f"M {fmt(sx)} {fmt(sy)} V {fmt(ey)} H {fmt(ex)}"
        return f"M {fmt(sx)} {fmt(sy)} H {fmt(ex)} V {fmt(ey)}"

    if kind == "bent3":
        # U-bend (both sites parallel) or Z-bend (perpendicular sites).
        if s_site in ("top", "bottom") and e_site in ("top", "bottom"):
            extend = bend_offset
            if s_site == "top":
                mid_y = min(sy, ey) - extend
            else:
                mid_y = max(sy, ey) + extend
            return f"M {fmt(sx)} {fmt(sy)} V {fmt(mid_y)} H {fmt(ex)} V {fmt(ey)}"
        if s_site in ("left", "right") and e_site in ("left", "right"):
            extend = bend_offset
            if s_site == "left":
                mid_x = min(sx, ex) - extend
            else:
                mid_x = max(sx, ex) + extend
            return f"M {fmt(sx)} {fmt(sy)} H {fmt(mid_x)} V {fmt(ey)} H {fmt(ex)}"
        # Mixed sites: collapse to an L-bend.
        if s_site in ("top", "bottom"):
            return f"M {fmt(sx)} {fmt(sy)} V {fmt(ey)} H {fmt(ex)}"
        return f"M {fmt(sx)} {fmt(sy)} H {fmt(ex)} V {fmt(ey)}"

    if kind in ("bent4", "bent5"):
        # 3-bend wrap: perpendicular out, sideways, perpendicular in. bent5
        # technically has 4 bends; we simplify to 3 since the extra middle
        # segment rarely carries meaning and is fiddly to default well.
        return _bent4_path(sx, sy, ex, ey, s_site, e_site, bend_offset, fmt)

    # Unknown bent shape — straight-line fallback the user can nudge by hand.
    return f"M {fmt(sx)} {fmt(sy)} L {fmt(ex)} {fmt(ey)}"


def _arrow_direction(line_el):
    """Read a:headEnd / a:tailEnd to decide arrow direction.

    OOXML calls the start of the line 'head' and the end 'tail'. So
    tailEnd type != 'none' means an arrowhead at the end point (forward).
    """
    if line_el is None:
        return "none"
    head = line_el.find("a:headEnd", NS)
    tail = line_el.find("a:tailEnd", NS)
    head_t = head.attrib.get("type", "none") if head is not None else "none"
    tail_t = tail.attrib.get("type", "none") if tail is not None else "none"
    fwd = tail_t and tail_t != "none"
    rev = head_t and head_t != "none"
    if fwd and rev:
        return "both"
    if fwd:
        return "forward"
    if rev:
        return "reverse"
    return "none"


_ANIM_PRESET_KIND = {
    "entr": "entrance",
    "exit": "exit",
    "emph": "emphasis",
    "path": "motion",
}


def extract_animations(root):
    """Walk a slide's `<p:timing>` tree and return a list of click-group records.

    Each record is `{kind: str, spids: [int, ...]}`. Click numbering is left to
    the caller (we just return the groups in document order). `kind` is the
    most common preset class within the group (`entrance` / `exit` /
    `emphasis` / `motion`); when multiple kinds mix in one group, the
    secondary counts are returned in `extra` as `{kind: count}`.

    `<p:bldLst><p:bldP build="p" spid="...">` markers — PPTX's per-paragraph
    build mode — are stored as `paragraph_build: True` on single-shape clicks
    that target a paragraph-built shape. Lets the emitter explain why a single
    text block consumes 10+ clicks.
    """
    if root is None:
        return []
    timing = root.find("p:timing", NS)
    if timing is None:
        return []

    # <p:bldLst><p:bldP build="p" spid="..."/> — paragraph build markers.
    # Different authoring tools use `build` vs `bld` for the attribute, so
    # check both. `build="p"` (or `bld="p"`) means each user click reveals one
    # paragraph of the target text shape.
    build_modes = {}
    for bldP in timing.iter("{%s}bldP" % NS["p"]):
        spid = bldP.attrib.get("spid")
        if not spid:
            continue
        bld = bldP.attrib.get("build") or bldP.attrib.get("bld") or ""
        if bld:
            build_modes[spid] = bld

    groups = []
    current = None

    # Flat scan of every <p:cTn> in document order. clickEffect starts a new
    # group; afterEffect/withEffect chain onto the current group.
    for cTn in timing.iter("{%s}cTn" % NS["p"]):
        node_type = cTn.attrib.get("nodeType")
        if node_type not in ("clickEffect", "afterEffect", "withEffect"):
            continue
        preset_class = cTn.attrib.get("presetClass", "entr")
        kind = _ANIM_PRESET_KIND.get(preset_class, preset_class or "entrance")

        spids = []
        for tgt in cTn.iter("{%s}spTgt" % NS["p"]):
            sp = tgt.attrib.get("spid")
            if sp:
                spids.append(sp)

        effect = {"kind": kind, "spids": spids}
        if node_type == "clickEffect" or current is None:
            groups.append({"effects": [effect]})
            current = groups[-1]
        else:
            current["effects"].append(effect)

    # Collapse each group's effects into a single record: dedup spids in order,
    # pick the most common kind, and report any secondary kinds.
    records = []
    for g in groups:
        seen = set()
        spids_ordered = []
        kind_counts = {}
        for eff in g["effects"]:
            kind_counts[eff["kind"]] = kind_counts.get(eff["kind"], 0) + 1
            for sp in eff["spids"]:
                if sp in seen:
                    continue
                seen.add(sp)
                spids_ordered.append(sp)
        if not spids_ordered:
            continue
        # Most common kind; ties broken by first appearance.
        primary = max(kind_counts, key=lambda k: (kind_counts[k], -list(kind_counts).index(k)))
        extra = {k: v for k, v in kind_counts.items() if k != primary}
        rec = {"kind": primary, "spids": spids_ordered}
        if extra:
            rec["extra_kinds"] = extra
        # Single-shape clicks targeting a paragraph-built shape get a tag so
        # the emitter can collapse the "N clicks all on shape #X" run into one
        # readable line.
        if len(spids_ordered) == 1 and build_modes.get(spids_ordered[0]) == "p":
            rec["paragraph_build"] = True
        records.append(rec)
    return records


def parse_slide(zf, slide_path, rels_path, deck_size=DEFAULT_DECK):
    root = parse_xml(zf, slide_path)
    if root is None:
        return {"error": f"could not parse {slide_path}"}

    shapes = []
    tables = []
    shape_by_id = {}
    deferred_connectors = []  # (elem, transform) — process after shapes are ready
    deferred_pictures = []

    for elem, transform in _walk_shapes(root):
        tag = elem.tag.split('}', 1)[-1]
        if tag == 'sp':
            cnv = elem.find("p:nvSpPr/p:cNvPr", NS)
            sp_id = cnv.attrib.get("id") if cnv is not None else None
            name = cnv.attrib.get("name", "") if cnv is not None else ""
            prst = ""
            spPr = elem.find("p:spPr", NS)
            if spPr is not None:
                prst_el = spPr.find("a:prstGeom", NS)
                if prst_el is not None:
                    prst = prst_el.attrib.get("prst", "")
            bbox = apply_transform(get_xfrm(elem), transform)
            fill = _fill_color(spPr)
            shape = {
                "id": sp_id,
                "name": name,
                "prst": prst,
                "bbox": bbox,
                "text": extract_paragraphs(elem),
                "fill": fill,
            }
            vert = _text_rotation(elem)
            if vert is not None:
                shape["vert"] = vert
            if _is_full_slide_overlay(bbox, fill, deck_size):
                shape["overlay"] = True
            shapes.append(shape)
            if sp_id:
                shape_by_id[sp_id] = shape
        elif tag == 'cxnSp':
            deferred_connectors.append((elem, transform))
        elif tag == 'pic':
            deferred_pictures.append((elem, transform))
        elif tag == 'graphicFrame':
            tbl = elem.find("a:graphic/a:graphicData/a:tbl", NS)
            if tbl is not None:
                tables.append(_parse_table(elem, tbl, transform))

    connectors = []
    for cxn, transform in deferred_connectors:
        cnv = cxn.find("p:nvCxnSpPr/p:cNvPr", NS)
        name = cnv.attrib.get("name", "") if cnv is not None else ""
        cxn_id = cnv.attrib.get("id") if cnv is not None else None
        prst = ""
        spPr = cxn.find("p:spPr", NS)
        line_el = None
        if spPr is not None:
            prst_el = spPr.find("a:prstGeom", NS)
            if prst_el is not None:
                prst = prst_el.attrib.get("prst", "")
            line_el = spPr.find("a:ln", NS)

        st_el = cxn.find("p:nvCxnSpPr/p:cNvCxnSpPr/a:stCxn", NS)
        en_el = cxn.find("p:nvCxnSpPr/p:cNvCxnSpPr/a:endCxn", NS)
        bbox = apply_transform(get_xfrm(cxn), transform)

        # Compute snapped endpoints when possible; fall back to bbox geometry.
        fb_start, fb_end = _bbox_endpoints(bbox)
        start = end = None
        if st_el is not None:
            sid = st_el.attrib.get("id")
            sidx = int(st_el.attrib.get("idx", "-1")) if st_el.attrib.get("idx") else None
            target = shape_by_id.get(sid)
            if target is not None:
                start = _shape_snap_point(target, sidx)
        if en_el is not None:
            eid = en_el.attrib.get("id")
            eidx = int(en_el.attrib.get("idx", "-1")) if en_el.attrib.get("idx") else None
            target = shape_by_id.get(eid)
            if target is not None:
                end = _shape_snap_point(target, eidx)
        if start is None:
            start = fb_start
        if end is None:
            end = fb_end

        record = {
            "id": cxn_id,
            "name": name,
            "prst": prst,
            "kind": _classify_kind(prst),
            "bbox": bbox,
            "start": start,
            "end": end,
            "arrow": _arrow_direction(line_el),
            "snapped": bool(start and start.get("shape_id")) and bool(end and end.get("shape_id")),
        }
        record["path"] = _suggest_path(record)
        connectors.append(record)

    image_refs = parse_rels(zf, rels_path)
    pictures = []
    for pic, transform in deferred_pictures:
        cnv = pic.find("p:nvPicPr/p:cNvPr", NS)
        name = cnv.attrib.get("name", "") if cnv is not None else ""
        pic_id = cnv.attrib.get("id") if cnv is not None else None
        blip = pic.find(".//a:blip", NS)
        rid = blip.attrib.get("{%s}embed" % NS["r"], "") if blip is not None else ""
        record = {
            "id": pic_id,
            "name": name,
            "bbox": apply_transform(get_xfrm(pic), transform),
            "file": image_refs.get(rid),
        }
        crop = _parse_src_rect(pic)
        if crop is not None:
            record["crop"] = crop
        pictures.append(record)

    return {
        "shapes": shapes,
        "connectors": connectors,
        "pictures": pictures,
        "tables": tables,
        "_raw_animations": extract_animations(root),
    }


def copy_thumbnails(pptx_path, dest_dir):
    """Copy `<pptx-stem>.thumbnails/slide-N.png` into `<dest_dir>/_thumbnails/`.

    The thumbnails directory is produced by `google-slides-export` (Slides API
    server-side render) — having a PNG of each source slide lets Claude *see*
    the slide instead of inferring layout from raw coordinates. Returns a
    dict `{slide_index: relative_path_from_dest_dir}` for everything copied;
    empty dict if no thumbnails source is found.
    """
    src_dir = os.path.splitext(pptx_path)[0] + ".thumbnails"
    if not os.path.isdir(src_dir):
        return {}
    dest_sub = os.path.join(dest_dir, "_thumbnails")
    os.makedirs(dest_sub, exist_ok=True)
    out = {}
    for name in sorted(os.listdir(src_dir)):
        m = re.match(r"slide-(\d+)\.png$", name)
        if not m:
            continue
        idx = int(m.group(1))
        shutil.copyfile(os.path.join(src_dir, name), os.path.join(dest_sub, name))
        out[idx] = f"./_thumbnails/{name}"
    return out


def load_videos_sidecar(pptx_path):
    """Return `{slide_index: [video, ...]}` from `<pptx-stem>.videos.json`.

    The sidecar is produced by `google-slides-export`'s Slides-API pass and
    recovers videos that PPTX export silently flattens to thumbnails. Missing
    sidecar is fine — returns an empty dict.
    """
    sidecar_path = os.path.splitext(pptx_path)[0] + ".videos.json"
    if not os.path.isfile(sidecar_path):
        return {}
    try:
        with open(sidecar_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"Warning: could not read {sidecar_path}: {e}\n")
        return {}
    return {s["index"]: s.get("videos", []) for s in data.get("slides", [])}


def _bbox_near(a, b, tol=5.0):
    """True if two bboxes (`{x,y,w,h}`) line up within `tol` px on every edge."""
    if not a or not b or a.get("x") is None or b.get("x") is None:
        return False
    return (
        abs(a["x"] - b["x"]) < tol
        and abs(a["y"] - b["y"]) < tol
        and abs(a["w"] - b["w"]) < tol
        and abs(a["h"] - b["h"]) < tol
    )


def annotate_video_thumbnails(slide):
    """Flag pictures that overlap a video's bbox as the video's static thumbnail.

    Google's PPTX export drops the video and inserts a placeholder picture at
    the same position. Marking those pictures lets Claude skip them when
    rendering the slide — the `<video>` / iframe / `<Youtube>` embed should
    take their place.
    """
    videos = slide.get("videos") or []
    if not videos:
        return
    for pic in slide.get("pictures") or []:
        pb = pic.get("bbox") or {}
        for v in videos:
            if _bbox_near(pb, v.get("bbox")):
                pic["video_placeholder"] = True
                break


def parse_notes(zf, notes_path):
    """Extract speaker notes, filtering out the slide-number placeholder."""
    root = parse_xml(zf, notes_path)
    if root is None:
        return ""
    parts = []
    for sp in root.iter("{%s}sp" % NS["p"]):
        ph = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
        ph_type = ph.attrib.get("type", "") if ph is not None else ""
        if ph_type == "sldImg":
            continue
        for para in extract_paragraphs(sp):
            text = para["text"].strip()
            if re.fullmatch(r"\d+", text):
                continue
            parts.append(text)
    return "\n".join(parts).strip()


def _run_tag(r):
    """Compact label describing a run's formatting deviations from the default.

    Order: bold, italic, strike, underline, color. Single-letter flags collapse
    into one token (e.g. `bs` for bold+strike); color stays separate after a `+`.
    """
    flags = ""
    if r.get("bold"):
        flags += "b"
    if r.get("italic"):
        flags += "i"
    if r.get("strike"):
        flags += "s"
    if r.get("underline"):
        flags += "u"
    parts = []
    if flags:
        parts.append(flags)
    if r.get("color"):
        parts.append("#" + r["color"])
    return "+".join(parts) if parts else "default"


def _is_formatted(r):
    return bool(
        r.get("bold") or r.get("italic")
        or r.get("strike") or r.get("underline")
        or r.get("color")
    )


def _slide_plain_text(slide):
    """Concatenated plain text of every paragraph on the slide, for fingerprinting."""
    parts = []
    for sh in slide.get("shapes", []):
        for p in sh.get("text", []):
            parts.append(p["text"])
    return "\n".join(parts).strip()


_BASIC_PRESETS = {"rect", "roundRect", "ellipse", "oval", "diamond", "rhombus"}


def _mermaidable(slide):
    """Decide if a slide's diagram could be re-expressed as a Mermaid flowchart.

    Returns a hint string (e.g. "LR" / "TB") when the slide looks like a clean
    node-edge graph, or None when it carries spatial meaning Mermaid would lose.
    """
    shapes = slide.get("shapes", []) or []
    cxns = slide.get("connectors", []) or []
    pics = slide.get("pictures", []) or []
    text_shapes = [s for s in shapes if any(p.get("text", "").strip() for p in s.get("text", []))]
    if pics or len(text_shapes) < 2 or not cxns:
        return None
    if any(s.get("prst") not in _BASIC_PRESETS for s in text_shapes):
        return None
    if not all(c.get("snapped") for c in cxns):
        return None
    # Direction hint from connector vectors.
    hsum = vsum = 0
    for c in cxns:
        st = c.get("start") or {}
        en = c.get("end") or {}
        if None in (st.get("x"), st.get("y"), en.get("x"), en.get("y")):
            continue
        hsum += abs(en["x"] - st["x"])
        vsum += abs(en["y"] - st["y"])
    return "LR" if hsum >= vsum else "TB"


def _bboxes_overlap(a, b):
    """True if two `{x, y, w, h}` bboxes overlap by any positive area."""
    if not a or not b:
        return False
    if a.get("x") is None or b.get("x") is None:
        return False
    ax, ay = a["x"], a["y"]
    aw, ah = a.get("w") or 0, a.get("h") or 0
    bx, by = b["x"], b["y"]
    bw, bh = b.get("w") or 0, b.get("h") or 0
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def _image_swap_collapse_signals(prev_slide, curr_slide):
    """Reasons to collapse adjacent picture-swap slides into one Slidev slide.

    Returns a list of human-readable signals — non-empty means "collapse",
    empty means "recommend N separate slides". The three signals catch the
    three legitimate uses of an image swap stack:

      - shared title/heading: same plain text across both slides → "same
        rhetorical beat, different illustration",
      - overlapping picture bboxes: the pictures stack on top of each other
        (one is the base, others reveal regions) → layered swap,
      - constant overlay shapes: every non-picture shape on the slide stayed
        put (callouts annotating a changing photo) → stable overlay.

    All other cases — disconnected illustrative examples, headerless picture
    grids — should stay as N separate slides.
    """
    signals = []

    prev_plain = _slide_plain_text(prev_slide).strip()
    curr_plain = _slide_plain_text(curr_slide).strip()
    if prev_plain and prev_plain == curr_plain:
        signals.append("shared heading/text across both slides")

    prev_pics = prev_slide.get("pictures") or []
    curr_pics = curr_slide.get("pictures") or []
    for pp in prev_pics:
        if pp.get("video_placeholder"):
            continue
        for cp in curr_pics:
            if cp.get("video_placeholder"):
                continue
            if pp.get("file") == cp.get("file"):
                continue
            if _bboxes_overlap(pp.get("bbox"), cp.get("bbox")):
                signals.append("picture bboxes overlap (layered swap, not alternatives)")
                break
        else:
            continue
        break

    prev_shape_keys = {
        _shape_pos_key(s)
        for s in (prev_slide.get("shapes") or [])
        if (s.get("bbox") or {}).get("x") is not None
    }
    curr_shape_keys = {
        _shape_pos_key(s)
        for s in (curr_slide.get("shapes") or [])
        if (s.get("bbox") or {}).get("x") is not None
    }
    if prev_shape_keys and prev_shape_keys == curr_shape_keys:
        signals.append("constant non-picture overlay shapes (callouts annotating the swap)")

    return signals


def _slide_picture_signature(slide):
    """Sorted tuple of image filenames on a slide — order-independent identity.

    Used to tell apart "same text, different highlight" (HIGHLIGHT-REVEAL) from
    "same text, different photos" (IMAGE-SWAP-REVEAL). Picture bbox/crop are
    ignored on purpose — minor jitter shouldn't break the match.
    """
    files = []
    for pic in slide.get("pictures") or []:
        f = pic.get("file")
        if f:
            files.append(f)
    return tuple(sorted(files))


def _slide_format_signature(slide):
    """Tuple of (text, tag) per run on the slide. Differs between highlight states."""
    sig = []
    for sh in slide.get("shapes", []):
        for p in sh.get("text", []):
            for r in p.get("runs", []) or []:
                if r.get("text", "").strip():
                    sig.append((r["text"], _run_tag(r)))
    return tuple(sig)


def _round_pos(v, step=0.5):
    """Quantize a coordinate so tiny drift between adjacent slides doesn't break matching."""
    if v is None:
        return None
    return round(v / step) * step


def _shape_text(sh):
    return " | ".join(p["text"] for p in sh.get("text", []))


# Thresholds for the "freeform / hand-drawn figure" heuristic. A slide with
# this many positioned shapes, at least this fraction lacking any text, AND
# this many empty shapes in absolute terms is almost always a decorative
# drawing (chalkboard X/O, neural-net mesh, …) that isn't worth recreating in
# `<Diagram>` — the source thumbnail is the better rendering.
#
# Three-gate design tuned against the "Why is AI useful for thinking about
# biological intelligence" deck: catches slide 11 (X/O game, 30 shapes / 18
# empty) and slide 36 (network mesh, 17 / 16) without firing on perceptron
# build-up slides 29–35 (≤ 16 shapes, ≤ 7 empty). The absolute `_MIN_EMPTY`
# gate is what stops the perceptron slides from sliding through purely on
# their early-build ratios.
_FREEFORM_MIN_SHAPES = 12
_FREEFORM_EMPTY_RATIO = 0.55
_FREEFORM_MIN_EMPTY = 12


def _is_labeled_grid(shapes):
    """True if the slide's empty shapes form a column-aligned or labeled-grid
    pattern — i.e. the figure is NOT freeform/hand-drawn despite the empty-shape
    ratio gate firing.

    Two signals:
      1. ≥ 80% of empty shapes share an X coordinate (one column of, say,
         labeled circles) — labels typically sit in a separate column.
      2. ≥ 80% of empty shapes have a non-empty sibling within `2 × shape_width`
         horizontally and roughly the same vertical band (label-beside pattern).

    Catches the "two columns of 6 ellipses + 6 label rects" structure in talk
    22 slides 5/6/7 — 12 empty shapes that the raw heuristic mistakes for
    freeform clutter.
    """
    empty = []
    non_empty = []
    for s in shapes:
        bb = s.get("bbox") or {}
        if bb.get("x") is None:
            continue
        has_text = any(p.get("text", "").strip() for p in s.get("text", []) or [])
        (non_empty if has_text else empty).append(s)
    if not empty:
        return False

    # Column alignment: cluster X coords with a 12-px tolerance and check whether
    # any single cluster captures ≥ 80% of the empty shapes.
    xs = [s["bbox"]["x"] for s in empty]
    tol = 12.0
    for ref_x in xs:
        same = sum(1 for x in xs if abs(x - ref_x) < tol)
        if same / len(xs) >= 0.8:
            return True

    # Labeled-sibling pattern: each empty shape has a non-empty shape within
    # 2× its own width horizontally, with overlapping vertical extents.
    if not non_empty:
        return False
    labeled = 0
    for e in empty:
        ebb = e["bbox"]
        ew = ebb.get("w") or 0
        ecx = ebb["x"] + ew / 2
        ecy = ebb["y"] + (ebb.get("h") or 0) / 2
        reach = max(ew, 1) * 2
        for ne in non_empty:
            nbb = ne["bbox"]
            if nbb.get("x") is None:
                continue
            ncx = nbb["x"] + (nbb.get("w") or 0) / 2
            n_top = nbb["y"]
            n_bot = nbb["y"] + (nbb.get("h") or 0)
            if abs(ncx - ecx) <= reach and (n_top - 8) <= ecy <= (n_bot + 8):
                labeled += 1
                break
    return labeled / len(empty) >= 0.8


def _freeform_figure_stats(slide):
    """Return (n_shapes, n_empty, is_freeform) for the freeform-figure heuristic.

    Only counts positioned shapes (those that survive the diff/emit gate
    `bbox.x is not None`). Tables, pictures, and connectors are *not* shapes
    here — they live on their own slide-level lists. An "empty" shape is one
    where every paragraph's text is whitespace-only.

    A second-stage check (`_is_labeled_grid`) gates the flag back off when the
    "empty shapes" look like the unlabeled member of a labeled-grid pair —
    avoids false-positives on perceptron-style schematics drawn as two columns
    of circles with sibling label rects.
    """
    shapes = [
        s for s in (slide.get("shapes") or [])
        if (s.get("bbox") or {}).get("x") is not None
    ]
    n_shapes = len(shapes)
    if n_shapes == 0:
        return (0, 0, False)
    n_empty = 0
    for s in shapes:
        if not any(p.get("text", "").strip() for p in s.get("text", []) or []):
            n_empty += 1
    ratio = n_empty / n_shapes
    is_freeform = (
        n_shapes >= _FREEFORM_MIN_SHAPES
        and ratio >= _FREEFORM_EMPTY_RATIO
        and n_empty >= _FREEFORM_MIN_EMPTY
    )
    if is_freeform and _is_labeled_grid(shapes):
        is_freeform = False
    return (n_shapes, n_empty, is_freeform)


# Thresholds for the "decorative sliver" heuristic. PPTX decks sometimes
# overlay many thin cropped strips of one image to fake a parallax/stripe
# effect; the analysis dutifully lists each strip but they add no information
# and crowd out the actual content. We only collapse when there's a meaningful
# pile of slivers AND most of them are aggressively cropped — false positives
# that suppress real content are worse than false negatives that leave them in.
_SLIVER_MIN_COUNT = 5
_SLIVER_CROP_MIN = 50.0   # % inset on at least one edge
_SLIVER_CROP_FRAC = 0.80  # share of group members that must meet that crop bar


def _is_sliver(pic):
    """True if a picture has any edge inset >= _SLIVER_CROP_MIN%."""
    crop = pic.get("crop") or {}
    if not crop:
        return False
    return any(
        (crop.get(edge) or 0) > _SLIVER_CROP_MIN for edge in ("l", "t", "r", "b")
    )


def _sliver_groups(pictures):
    """Group pictures by filename and return {file: [sliver_pic, …]} for groups
    that look like decorative-sliver overlays.

    A group qualifies when it has >= _SLIVER_MIN_COUNT slivers AND >=
    _SLIVER_CROP_FRAC of the same-file pictures are slivers. Uncropped (or
    mildly cropped) instances of the same file are NOT included in the
    returned list — those still emit normally.
    """
    if not pictures:
        return {}
    by_file = {}
    for p in pictures:
        f = p.get("file")
        if not f:
            continue
        by_file.setdefault(f, []).append(p)
    groups = {}
    for f, group in by_file.items():
        slivers = [p for p in group if _is_sliver(p)]
        if (
            len(slivers) >= _SLIVER_MIN_COUNT
            and len(slivers) / len(group) >= _SLIVER_CROP_FRAC
        ):
            groups[f] = slivers
    return groups


# Thresholds for the "scene change" annotation on a diff block. When slide N+1
# wipes most of slide N's shapes and adds new ones, it's a fresh slide that
# happens to come after — not a build-up. The skill's "one diff = one click"
# rule doesn't apply; the author needs to see that explicitly.
#
# Two trigger paths: (1) ≥ 70% of a 5+ shape prior is wiped, OR (2) 100% of
# the prior's shapes are wiped regardless of count — that's a scene change
# even when going from 1 shape to N (e.g. a bare title slide → content slide).
_SCENE_CHANGE_MIN_PRIOR = 5
_SCENE_CHANGE_REMOVED_RATIO = 0.7

# Threshold for the "text-swap scene change" annotation. A single shape stays
# put across slides but its text is replaced with unrelated content (Jaccard
# token similarity at-or-below this value). Detects the "stable banner with
# swapping bullet content" pattern that looks like a no-op build-up but is
# actually N separate slides.
_TEXT_SWAP_MAX_JACCARD = 0.15


def _jaccard_tokens(a, b):
    """Word-token Jaccard similarity in [0, 1]. Used to decide whether two
    shape-text strings are "unrelated enough" to call a scene change.

    Two empty strings count as identical (1.0); one empty and one non-empty
    counts as fully different (0.0).
    """
    toks_a = set(re.findall(r"\w+", (a or "").lower()))
    toks_b = set(re.findall(r"\w+", (b or "").lower()))
    if not toks_a and not toks_b:
        return 1.0
    if not toks_a or not toks_b:
        return 0.0
    return len(toks_a & toks_b) / len(toks_a | toks_b)


def _shape_pos_key(sh):
    bb = sh.get("bbox") or {}
    return (
        sh.get("prst", ""),
        _round_pos(bb.get("x")),
        _round_pos(bb.get("y")),
        _round_pos(bb.get("w")),
        _round_pos(bb.get("h")),
    )




def _connector_key(c):
    st = c.get("start") or {}
    en = c.get("end") or {}
    return (
        c.get("kind", ""),
        _round_pos(st.get("x")), _round_pos(st.get("y")),
        _round_pos(en.get("x")), _round_pos(en.get("y")),
        c.get("arrow", "none"),
    )


def _picture_key(pic):
    bb = pic.get("bbox") or {}
    crop = pic.get("crop") or {}
    return (
        pic.get("file", ""),
        _round_pos(bb.get("x")), _round_pos(bb.get("y")),
        _round_pos(bb.get("w")), _round_pos(bb.get("h")),
        crop.get("l", 0), crop.get("t", 0), crop.get("r", 0), crop.get("b", 0),
    )


def _diff_by_key(prev_items, curr_items, key_fn):
    """Match items by key_fn; return (added, removed, paired).

    paired is a list of (prev_item, curr_item) at the same key — caller can
    inspect those for non-key differences (e.g. text changes on a shape with
    unchanged geometry).
    """
    prev_by = {}
    curr_by = {}
    for it in prev_items:
        prev_by.setdefault(key_fn(it), []).append(it)
    for it in curr_items:
        curr_by.setdefault(key_fn(it), []).append(it)
    added, removed, paired = [], [], []
    for k in set(prev_by) | set(curr_by):
        p_list = prev_by.get(k, [])
        c_list = curr_by.get(k, [])
        n_pairs = min(len(p_list), len(c_list))
        for i in range(n_pairs):
            paired.append((p_list[i], c_list[i]))
        if len(p_list) > n_pairs:
            removed.extend(p_list[n_pairs:])
        if len(c_list) > n_pairs:
            added.extend(c_list[n_pairs:])
    return added, removed, paired


def _shape_one_line(sh):
    bb = sh.get("bbox") or {}
    txt = _shape_text(sh)
    fill_tag = f" fill={sh['fill']}" if sh.get("fill") else ""
    return f"`{sh.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}{fill_tag}  text={txt!r}"


def _connector_one_line(c):
    st = c.get("start") or {}
    en = c.get("end") or {}
    arrow_glyph = {"forward": "→", "reverse": "←", "both": "↔", "none": "—"}
    glyph = arrow_glyph.get(c.get("arrow", "none"), "—")
    return f"`{c.get('kind', '?')}` (arrow={c.get('arrow')}): ({st.get('x')}, {st.get('y')}) {glyph} ({en.get('x')}, {en.get('y')})"


def _picture_one_line(pic):
    bb = pic.get("bbox") or {}
    crop = pic.get("crop")
    crop_tag = ""
    if crop:
        crop_tag = f" ✂ crop l={crop['l']}% t={crop['t']}% r={crop['r']}% b={crop['b']}%"
    return f"`{pic.get('file', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}{crop_tag}"


def _emit_diff(L, prev_slide, curr_slide, *, limit=40):
    """Append a per-transition diff block to L. No-op if there's no prior slide
    or if the slides are identical at the shape/connector/picture level.

    A single diff block represents ONE source-slide transition — if the author
    revealed five shapes between these two slides, all five should share the
    same `revealAt` in the resulting Slidev build-up. See SKILL.md.
    """
    if prev_slide is None:
        return
    prev_shapes = [s for s in prev_slide.get("shapes", []) or []
                   if (s.get("bbox") or {}).get("x") is not None]
    curr_shapes = [s for s in curr_slide.get("shapes", []) or []
                   if (s.get("bbox") or {}).get("x") is not None]

    s_added, s_removed, s_paired = _diff_by_key(prev_shapes, curr_shapes, _shape_pos_key)
    # A "modification" on a stable shape is either a text edit or a recolor
    # (the grayscale-activity decks rely on the latter for build-ups).
    s_modified = [
        (p, c) for (p, c) in s_paired
        if _shape_text(p) != _shape_text(c) or p.get("fill") != c.get("fill")
    ]

    c_added, c_removed, _ = _diff_by_key(
        prev_slide.get("connectors", []) or [],
        curr_slide.get("connectors", []) or [],
        _connector_key,
    )
    p_added, p_removed, _ = _diff_by_key(
        prev_slide.get("pictures", []) or [],
        curr_slide.get("pictures", []) or [],
        _picture_key,
    )

    total = (len(s_added) + len(s_removed) + len(s_modified)
             + len(c_added) + len(c_removed) + len(p_added) + len(p_removed))
    if total == 0:
        return

    # Scene-change detection: if slide N+1 wipes most of slide N's shapes, the
    # "one diff = one click" build-up rule doesn't apply. Swap the header so
    # the author knows to treat this transition as a fresh slide.
    #
    # Two scene-change kinds are detected here:
    #   - "shape scene change" — most of the prior shapes are gone and new ones
    #     replace them (the standard case).
    #   - "text-swap scene change" — every shape stayed put but the *only*
    #     change is a text replacement on a single shape, with the new text
    #     sharing no tokens with the old. The "stable banner with rotating
    #     content" pattern from talk-22 slides 27–30.
    n_prior = len(prev_shapes)
    n_added = len(s_added)
    n_removed = len(s_removed)
    removed_ratio = n_removed / max(n_prior, 1) if n_prior else 0
    scene_change = (
        # All-or-nothing wipe regardless of prior count — catches title → body
        # transitions that the 5-shape gate would miss.
        (n_prior >= 1 and n_removed == n_prior and n_added >= 1)
        # Mostly-wiped: the original 70%-of-5+ threshold.
        or (
            n_prior >= _SCENE_CHANGE_MIN_PRIOR
            and removed_ratio >= _SCENE_CHANGE_REMOVED_RATIO
            and n_added >= 1
        )
    )
    curr_slide["scene_change"] = scene_change

    text_swap_scene_change = False
    text_swap_detail = None
    if (
        not scene_change
        and not s_added and not s_removed
        and not c_added and not c_removed
        and not p_added and not p_removed
        and len(s_modified) == 1
    ):
        prev_sh, curr_sh = s_modified[0]
        prev_text = _shape_text(prev_sh)
        curr_text = _shape_text(curr_sh)
        fill_unchanged = prev_sh.get("fill") == curr_sh.get("fill")
        if (
            fill_unchanged
            and prev_text != curr_text
            and (prev_text.strip() or curr_text.strip())
            and _jaccard_tokens(prev_text, curr_text) <= _TEXT_SWAP_MAX_JACCARD
        ):
            text_swap_scene_change = True
            bb = (curr_sh.get("bbox") or {})
            text_swap_detail = (
                f"shape at ({bb.get('x')}, {bb.get('y')}) "
                f"replaced its text with unrelated content"
            )
    curr_slide["text_swap_scene_change"] = text_swap_scene_change

    L.append("")
    if scene_change:
        L.append(
            f"**Diff from slide {prev_slide['index']}** "
            f"⛔ **scene change** (prior shapes removed wholesale — treat slide "
            f"{curr_slide['index']} as a fresh slide, NOT a build-up click):"
        )
    elif text_swap_scene_change:
        L.append(
            f"**Diff from slide {prev_slide['index']}** "
            f"⛔ **text-swap scene change** ({text_swap_detail}; the new text "
            f"shares no tokens with the old — treat slide "
            f"{curr_slide['index']} as a fresh slide, NOT a click-driven swap):"
        )
    else:
        L.append(
            f"**Diff from slide {prev_slide['index']}** "
            f"(if this is a build-up, treat the whole block as **one click** — every entry below shares the same `revealAt`):"
        )

    def emit_list(label, items, formatter):
        L.append(f"- {label} ({len(items)}):")
        for it in items[:limit]:
            L.append(f"  - {formatter(it)}")
        if len(items) > limit:
            L.append(f"  - … and {len(items) - limit} more (see full shape list below)")

    def emit_picture_list(label, items):
        """Like emit_list, but collapses decorative-sliver groups into one
        summary line per source file. The count in the header is the *real*
        item count (unchanged) so the click semantics stay inspectable; only
        the per-entry rendering changes.
        """
        groups = _sliver_groups(items)
        if not groups:
            emit_list(label, items, _picture_one_line)
            return
        sliver_ids = set()
        for fname, slivers in groups.items():
            for s in slivers:
                sliver_ids.add(id(s))
        L.append(f"- {label} ({len(items)}):")
        # Emit non-sliver pictures normally (truncated to `limit`); then emit
        # one summary line per collapsed sliver group. We don't count the
        # summary lines against `limit` — collapsing the slivers is the
        # whole point.
        non_slivers = [it for it in items if id(it) not in sliver_ids]
        for it in non_slivers[:limit]:
            L.append(f"  - {_picture_one_line(it)}")
        if len(non_slivers) > limit:
            L.append(f"  - … and {len(non_slivers) - limit} more (see full picture list below)")
        for fname, slivers in groups.items():
            L.append(
                f"  - `{fname}` — {len(slivers)} decorative slivers "
                f"(cropped views of the same image, likely a parallax/stripe "
                f"overlay; not load-bearing)"
            )

    if s_added:
        emit_list("added shapes", s_added, _shape_one_line)
    if s_removed:
        emit_list("removed shapes", s_removed, _shape_one_line)
    if s_modified:
        L.append(f"- text/fill changes on existing shapes ({len(s_modified)}):")
        for prev_sh, curr_sh in s_modified[:limit]:
            bb = curr_sh.get("bbox") or {}
            changes = []
            if _shape_text(prev_sh) != _shape_text(curr_sh):
                changes.append(f"text {_shape_text(prev_sh)!r} → {_shape_text(curr_sh)!r}")
            if prev_sh.get("fill") != curr_sh.get("fill"):
                changes.append(f"fill {prev_sh.get('fill') or '(none)'} → {curr_sh.get('fill') or '(none)'}")
            L.append(
                f"  - `{curr_sh.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}): "
                + "; ".join(changes)
            )
        if len(s_modified) > limit:
            L.append(f"  - … and {len(s_modified) - limit} more")
    if c_added:
        emit_list("added connectors", c_added, _connector_one_line)
    if c_removed:
        emit_list("removed connectors", c_removed, _connector_one_line)
    if p_added:
        emit_picture_list("added pictures", p_added)
    if p_removed:
        emit_picture_list("removed pictures", p_removed)


def _finalize_animations(slide):
    """Filter the slide's raw animation groups to surviving shapes, assign
    click numbers, and stash the result on the slide.

    Returns the final list of `{click, kind, spids, extra_kinds?}` records
    (also stored as `slide["animations"]` when non-empty). Strips the
    `_raw_animations` intermediate either way so the emitted JSON stays tidy.
    """
    raw = slide.pop("_raw_animations", None) or []
    # "Surviving" = the same gate the markdown shape listing uses (positioned
    # bbox). PPTX animations can target shapes, pictures, or connectors — all
    # share the slide-level cNvPr id namespace, so check every kind.
    alive = set()
    for sh in slide.get("shapes") or []:
        sid = sh.get("id")
        if sid and (sh.get("bbox") or {}).get("x") is not None:
            alive.add(str(sid))
    for pic in slide.get("pictures") or []:
        pid = pic.get("id")
        if pid and (pic.get("bbox") or {}).get("x") is not None:
            alive.add(str(pid))
    for cxn in slide.get("connectors") or []:
        cid = cxn.get("id")
        if cid and (cxn.get("bbox") or {}).get("x") is not None:
            alive.add(str(cid))

    final = []
    click = 0
    for grp in raw:
        spids_str = [sp for sp in grp.get("spids", []) if sp in alive]
        if not spids_str:
            continue
        # PPTX cNvPr ids are unsignedInt — emit numeric when parseable, fall
        # back to the raw string token so we never lose a real target.
        spids = []
        for sp in spids_str:
            try:
                spids.append(int(sp))
            except (TypeError, ValueError):
                spids.append(sp)
        click += 1
        rec = {"click": click, "kind": grp.get("kind", "entrance"), "spids": spids}
        if grp.get("extra_kinds"):
            # Re-filter extra_kinds counts to nothing-special; keep as-is since
            # they describe the *effects*, not the specific spids dropped above.
            rec["extra_kinds"] = grp["extra_kinds"]
        if grp.get("paragraph_build"):
            rec["paragraph_build"] = True
        final.append(rec)

    if final:
        slide["animations"] = final
    return final


def _format_kind_tag(rec):
    kind = rec.get("kind", "entrance")
    extra_kinds = rec.get("extra_kinds") or {}
    if extra_kinds:
        extras = " + ".join(f"{v} {k}" for k, v in extra_kinds.items())
        return f" ({kind} + {extras})"
    if kind == "entrance":
        return " (entrance)"
    return f" ({kind})"


def _format_spids(spids):
    if len(spids) > 6:
        shown = ", ".join(f"#{sp}" for sp in spids[:5])
        return f"{shown} … and {len(spids) - 5} more"
    if len(spids) == 1:
        return f"shape #{spids[0]}"
    return "shapes " + ", ".join(f"#{sp}" for sp in spids)


def _emit_animations(L, animations, slide):
    """Append a 🎬 PPTX animation annotation block to L. No-op if empty.

    Consecutive single-spid clicks of the same kind collapse into one line.
    When the run targets a paragraph-built shape (`<p:bldP build="p">`), the
    line names the paragraph count from the shape's text so the author knows
    which click reveals which paragraph.
    """
    if not animations:
        return
    n = len(animations)
    L.append("")
    L.append(
        f"🎬 **PPTX animation** — {n} click{'s' if n != 1 else ''} built into "
        f"this slide. Group elements by click when mapping to `v-click` / "
        f"`revealAt`:"
    )

    # Paragraph counts per shape spid — used when a run is paragraph-built.
    para_counts = {}
    for sh in slide.get("shapes") or []:
        sid = sh.get("id")
        if sid is None:
            continue
        n_para = sum(
            1 for p in (sh.get("text") or []) if p.get("text", "").strip()
        )
        para_counts[str(sid)] = n_para

    i = 0
    while i < len(animations):
        rec = animations[i]
        if len(rec["spids"]) == 1:
            spid = rec["spids"][0]
            kind = rec["kind"]
            j = i + 1
            while (
                j < len(animations)
                and len(animations[j]["spids"]) == 1
                and animations[j]["spids"][0] == spid
                and animations[j]["kind"] == kind
                and not animations[j].get("extra_kinds")
                and not rec.get("extra_kinds")
            ):
                j += 1
            run = j - i
            paragraph_build = any(
                animations[k].get("paragraph_build") for k in range(i, j)
            )
            if run >= 3 or (paragraph_build and run >= 2):
                first_click = rec["click"]
                last_click = animations[j - 1]["click"]
                pcount = para_counts.get(str(spid))
                if paragraph_build:
                    extra_note = ""
                    if pcount is not None:
                        # PPTX often emits one extra click per paragraph beyond
                        # the visible count (sub-bullet wrappers); flag the
                        # mismatch so the author isn't confused.
                        mismatch = (
                            f" — note: PPTX has {run} click groups for "
                            f"{pcount} visible paragraph"
                            f"{'s' if pcount != 1 else ''}, so some clicks "
                            f"may reveal bullet-level sub-builds"
                            if pcount and run != pcount
                            else ""
                        )
                        extra_note = (
                            f"; shape #{spid} has `<p:bldP build=\"p\">` "
                            f"(paragraph-by-paragraph reveal)"
                            f"{mismatch}"
                        )
                    L.append(
                        f"- clicks {first_click}–{last_click}: shape #{spid} "
                        f"({kind} × {run}{extra_note})"
                    )
                else:
                    L.append(
                        f"- clicks {first_click}–{last_click}: shape #{spid} "
                        f"({kind} × {run} consecutive — likely a paragraph or "
                        f"bullet build on a single text shape)"
                    )
                i = j
                continue
        spid_str = _format_spids(rec["spids"])
        kind_tag = _format_kind_tag(rec)
        L.append(f"- click {rec['click']}: {spid_str}{kind_tag}")
        i += 1


def _build_shape_lines(slide):
    """Return the markdown lines for a slide's `**Shapes (px in deck coords):**`
    section. Splitting this out lets `write_summary` compare a slide's shape
    list to the prior slide's and elide identical bodies (long decks repeat
    huge shape lists slide-to-slide).
    """
    out = []
    for sh in slide.get("shapes", []):
        bb = sh.get("bbox") or {}
        if bb.get("x") is None:
            continue
        paragraphs = [p["text"] for p in sh.get("text", [])]
        sid = sh.get("id")
        id_tag = f"#{sid} " if sid else ""
        fill_tag = f" fill={sh['fill']}" if sh.get("fill") else ""
        vert = sh.get("vert")
        vert_tag = f"  vert={vert}" if vert is not None else ""
        overlay_tag = (
            "  🎨 full-slide overlay (likely a darken scrim over a background picture)"
            if sh.get("overlay") else ""
        )
        head = (
            f"- {id_tag}`{sh.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}) "
            f"size {bb.get('w')}×{bb.get('h')}{fill_tag}{vert_tag}{overlay_tag}"
        )
        # Single-paragraph (or empty) shapes keep the inline `text=` form so the
        # analysis stays scannable. Multi-paragraph shapes need each paragraph
        # on its own line — a fenced block is the only way to preserve line
        # breaks inside a markdown list item.
        if len(paragraphs) <= 1:
            txt = paragraphs[0] if paragraphs else ""
            out.append(f"{head}  text={txt!r}")
        else:
            out.append(head)
            out.append("  ```")
            for p in paragraphs:
                out.append(f"  {p}")
            out.append("  ```")
    return out


def _slide_one_liner(slide, limit=70):
    """Short TOC-friendly title for a slide. Uses the first non-empty paragraph
    of any shape, truncated. Falls back to '(blank)' for divider slides.
    """
    for sh in slide.get("shapes") or []:
        for p in sh.get("text") or []:
            t = (p.get("text") or "").strip()
            if t:
                # Collapse newlines and runs of whitespace.
                t = re.sub(r"\s+", " ", t)
                if len(t) > limit:
                    t = t[:limit - 1].rstrip() + "…"
                return t
    if slide.get("pictures"):
        n = len(slide["pictures"])
        return f"({n} picture{'s' if n != 1 else ''})"
    return "(blank)"


def _slide_toc_annotations(slide):
    """Return a list of icon tokens summarizing a slide's annotations.

    Reads fields stashed on the slide dict during the write pass — anything
    that's already shown inline in the slide section is surfaced here so the
    reader can scan the TOC and find the high-signal slides without reading
    the whole file.
    """
    tags = []
    if slide.get("freeform_figure"):
        tags.append("🪄")
    if slide.get("animations"):
        tags.append(f"🎬×{len(slide['animations'])}")
    if slide.get("scene_change"):
        tags.append("⛔")
    if slide.get("text_swap_scene_change"):
        tags.append("⛔text-swap")
    if slide.get("image_swap") == "collapse":
        tags.append("🔄")
    if slide.get("image_swap") == "split":
        tags.append("🔁")
    if slide.get("highlight_reveal"):
        tags.append("⚠")
    if slide.get("mermaid_hint"):
        tags.append(f"💡{slide['mermaid_hint']}")
    if slide.get("sticker_candidate"):
        tags.append(f"🪧×{slide['sticker_candidate']}")
    return tags


def write_summary(path, analysis):
    preamble = []
    preamble.append(f"# PPTX analysis: {analysis['pptx']}")
    preamble.append("")
    sz = analysis["deck_size"]
    preamble.append(f"- Deck size: **{sz['w']} × {sz['h']} px** — use as SVG `viewBox` for diagram slides.")
    imgs = analysis["extracted_images"]
    preamble.append(f"- Extracted images (co-located with slides.md): {', '.join(f'`{n}`' for n in imgs) if imgs else '(none)'}")
    preamble.append(f"- Slide count: {len(analysis['slides'])}")
    preamble.append("")
    preamble.append("> Look for **adjacent slides with overlapping text/shapes** — they are almost always build-up animations to collapse into one Slidev slide with `v-click` reveals.")
    preamble.append(">")
    preamble.append("> **Each `**Diff from slide N**` block below is ONE click in the build-up.** If a diff lists five new shapes, all five share the same `revealAt`. Don't fragment a single source-slide transition across multiple clicks — the author chose to reveal those elements together for a reason (a node and its label, a binary op's two inputs, a structure and its annotation). Number clicks by source-slide transition, not by element count.")
    preamble.append(">")
    preamble.append("> A common variant: adjacent slides with **identical plain text but different run formatting** (bold/color shifts). That's a highlight-reveal build, not a duplicate. The script flags these inline as `⚠ HIGHLIGHT-REVEAL …`. Collapse them into one slide whose runs toggle their `.active` class based on `$clicks`.")
    preamble.append("")

    prev_plain = None
    prev_sig = None
    prev_pics = None
    prev_index = None
    prev_slide = None
    prev_shape_lines = None
    prev_shape_idx = None
    if analysis.get("thumbnails_dir"):
        preamble.append(
            f"> 🖼  **Source thumbnails available**: every slide entry has a "
            f"`**Source:**` line pointing at a PNG render from "
            f"`{analysis['thumbnails_dir']}/`. **Read the PNG** before writing "
            f"the slide — it's the cheapest way to see what the original "
            f"actually looks like."
        )
        preamble.append("")

    # All per-slide content accumulates in `slide_body`; `L` is an alias kept
    # for the existing loop body (which calls helpers like `_emit_diff(L, …)`).
    # Don't rename to `body` — the table-emit code uses `body` as a local var.
    slide_body = []
    L = slide_body

    for s in analysis["slides"]:
        L.append(f"## Slide {s['index']}")

        if s.get("thumbnail"):
            L.append("")
            L.append(f"**Source:** `{s['thumbnail']}` — read this PNG first.")

        n_shapes_ff, n_empty_ff, is_freeform = _freeform_figure_stats(s)
        s["freeform_figure"] = is_freeform
        if is_freeform:
            L.append("")
            L.append(
                f"🪄 **Freeform/dense figure** ({n_shapes_ff} shapes, "
                f"{n_empty_ff} with no text) — likely hand-drawn or "
                f"decorative; consider `<img src=\"./_thumbnails/slide-"
                f"{s['index']}.png\">` over `<Diagram>`."
            )

        plain = _slide_plain_text(s)
        sig = _slide_format_signature(s)
        pics = _slide_picture_signature(s)
        if plain and plain == prev_plain:
            if pics != prev_pics and prev_slide is not None:
                signals = _image_swap_collapse_signals(prev_slide, s)
                if signals:
                    s["image_swap"] = "collapse"
                    L.append("")
                    L.append(
                        f"> 🔄 IMAGE-SWAP-REVEAL: same heading as slide "
                        f"{prev_index}, pictures differ ({'; '.join(signals)}). "
                        f"Collapse into one Slidev slide with v-click image "
                        f"reveals."
                    )
                else:
                    s["image_swap"] = "split"
                    L.append("")
                    L.append(
                        f"> 🔁 ADJACENT-PICTURE-SLIDES: same heading as slide "
                        f"{prev_index}, pictures differ — but no overlapping "
                        f"picture bboxes and no constant overlay shapes. Likely "
                        f"disconnected examples that happen to share a heading. "
                        f"**Recommend N separate `layout: image` slides with "
                        f"captions**, NOT a click-collapsed swap stack."
                    )
            elif sig != prev_sig:
                s["highlight_reveal"] = True
                L.append("")
                L.append(f"> ⚠ HIGHLIGHT-REVEAL: same plain text as slide {prev_index}, but per-run formatting differs. Collapse with slide {prev_index} into one Slidev slide where each segment toggles highlight on click.")
        elif (not plain) and (not prev_plain) and pics != prev_pics and prev_pics and prev_slide is not None:
            # Both slides headerless, pictures swap. No shared text to anchor
            # the rhetoric, so only collapse when there's a layered/overlay
            # signal; otherwise these are disconnected illustrative slides.
            signals = _image_swap_collapse_signals(prev_slide, s)
            if signals:
                s["image_swap"] = "collapse"
                L.append("")
                L.append(
                    f"> 🔄 IMAGE-SWAP-REVEAL: headerless picture slides "
                    f"({'; '.join(signals)}). Collapse into one Slidev slide."
                )
            else:
                s["image_swap"] = "split"
                L.append("")
                L.append(
                    f"> 🔁 ADJACENT-PICTURE-SLIDES: slide {prev_index} → "
                    f"{s['index']} both headerless, pictures swap, no constant "
                    f"overlay shapes. **Recommend N separate `layout: image` "
                    f"slides with captions** over a click-collapsed swap stack."
                )
        prev_plain, prev_sig, prev_pics, prev_index = plain, sig, pics, s["index"]

        mhint = _mermaidable(s)
        if mhint:
            s["mermaid_hint"] = mhint
            L.append("")
            L.append(f"> 💡 Mermaid candidate ({mhint}): all shapes are basic and all connectors snap to them — consider a `mermaid` block instead of hand-rolled SVG. Skip if the diagram's spatial layout is itself meaningful.")

        _emit_diff(L, prev_slide, s)
        prev_slide = s

        animations = _finalize_animations(s)
        _emit_animations(L, animations, s)

        # Text paragraphs across all shapes
        text_paras = []
        for sh in s.get("shapes", []):
            for p in sh.get("text", []):
                text_paras.append(p)
        if text_paras:
            L.append("")
            L.append("**Text:**")
            for p in text_paras:
                indent = "  " * p["level"]
                L.append(f"{indent}- {p['text']}")
                runs = p.get("runs") or []
                if any(_is_formatted(r) for r in runs):
                    for r in runs:
                        if not r.get("text", "").strip():
                            continue
                        snippet = r["text"]
                        if len(snippet) > 140:
                            snippet = snippet[:60] + " … " + snippet[-60:]
                        L.append(f"{indent}  - `[{_run_tag(r)}]` {snippet!r}")

        pics = s.get("pictures") or []
        if pics:
            L.append("")
            L.append("**Pictures:**")
            sliver_groups = _sliver_groups(pics)
            sliver_ids = set()
            for fname, slivers in sliver_groups.items():
                for sl in slivers:
                    sliver_ids.add(id(sl))
            s["sliver_groups"] = (
                {f: len(g) for f, g in sliver_groups.items()} or None
            )
            # Slidev canvas math for the per-picture `slidev pos` hint and the
            # `dragPos:` block below. Defaults to a 980-wide 16:9 canvas — same
            # defaults the `<Sticker>` component (and Slidev's `<v-drag>`) use.
            slidev_w = 980
            slidev_h = round(slidev_w * 9 / 16)
            deck_w = sz["w"] or 960
            deck_h = sz["h"] or 540
            def _slidev_pos(bb):
                x = round((bb.get("x") or 0) * slidev_w / deck_w)
                y = round((bb.get("y") or 0) * slidev_h / deck_h)
                w = round((bb.get("w") or 0) * slidev_w / deck_w)
                h = round((bb.get("h") or 0) * slidev_h / deck_h)
                return f"{x},{y},{w},{h}"
            placed = []  # (sticker_id, pos_str, file) for pics worth dragging
            for i, pic in enumerate(pics):
                if id(pic) in sliver_ids:
                    continue
                bb = pic.get("bbox") or {}
                placeholder_tag = (
                    "  ⚠ **video placeholder** — skip this picture and embed the matching video below instead"
                    if pic.get("video_placeholder") else ""
                )
                pos_str = _slidev_pos(bb)
                L.append(
                    f"- `{pic.get('file', '?')}` at ({bb.get('x')}, {bb.get('y')}) "
                    f"size {bb.get('w')}×{bb.get('h')} → slidev pos `{pos_str}`"
                    f"{placeholder_tag}"
                )
                crop = pic.get("crop")
                if crop:
                    L.append(
                        f"  - ✂ **crop** l={crop['l']}% t={crop['t']}% r={crop['r']}% b={crop['b']}% "
                        f"— source's full image is wider/taller than the bbox; only the visible portion shows. "
                        f"Wrap in `overflow:hidden` and scale the `<img>` up — see SKILL.md \"Cropped pictures\"."
                    )
                    L.append(
                        f"  - CSS values (percentages of the wrapper): "
                        f"`img {{ width: {crop['img_width_pct']}%; height: {crop['img_height_pct']}%; "
                        f"left: {crop['img_left_pct']}%; top: {crop['img_top_pct']}%; }}`"
                    )
                if not pic.get("video_placeholder") and not crop:
                    placed.append((f"pic-{i}", pos_str, pic.get("file") or "?"))
            # If a slide has 3+ free-floating pictures at irregular positions
            # (not a 2-col, not a gallery grid), it's a `<Sticker>` candidate.
            # Emit a ready-to-paste `dragPos:` block + Sticker tags so the
            # author can drop them in and refine with the Slidev drag editor.
            if len(placed) >= 3 and not s.get("image_swap") and not s.get("highlight_reveal"):
                s["sticker_candidate"] = len(placed)
                L.append("")
                L.append(
                    f"🪧 **Sticker candidate** ({len(placed)} free-floating "
                    f"pictures) — if these aren't a clean grid (gallery) or a "
                    f"single dominant figure (media/image), drop the block below "
                    f"into slide frontmatter and the tags into the body. Then "
                    f"`npm run dev` and **double-click any sticker** to drag / "
                    f"resize / rotate in place — the editor writes positions back "
                    f"to the `dragPos:` block."
                )
                L.append("")
                L.append("```yaml")
                L.append("dragPos:")
                for sid, pos_str, _f in placed:
                    L.append(f'  {sid}: "{pos_str}"')
                L.append("```")
                L.append("")
                L.append("```html")
                for sid, _pos, f in placed:
                    L.append(f'<Sticker id="{sid}" src="./{f}" />')
                L.append("```")
            for fname, slivers in sliver_groups.items():
                L.append(
                    f"- `{fname}` — {len(slivers)} decorative slivers "
                    f"(cropped views of the same image, likely a parallax/"
                    f"stripe overlay; not load-bearing)"
                )

        tbls = s.get("tables") or []
        if tbls:
            L.append("")
            L.append("**Tables:**")
            for t in tbls:
                bb = t.get("bbox") or {}
                L.append(
                    f"- {t.get('cols', '?')}-col × {t.get('rows', '?')}-row table "
                    f"at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}"
                )
                headers = t.get("headers")
                if headers is not None:
                    L.append(f"  Headers: {headers}")
                else:
                    L.append("  Headers: null")
                body = t.get("body") or []
                if body:
                    L.append("  Rows:")
                    for row in body:
                        L.append(f"  - {row}")

        vids = s.get("videos") or []
        if vids:
            L.append("")
            L.append("**Videos** (recovered from Slides API — PPTX export dropped these):")
            for v in vids:
                bb = v.get("bbox") or {}
                src = v.get("source") or "?"
                flags = []
                if v.get("autoplay"):
                    flags.append("autoplay")
                if v.get("mute"):
                    flags.append("muted")
                if v.get("start_seconds"):
                    flags.append(f"start={v['start_seconds']}s")
                if v.get("end_seconds"):
                    flags.append(f"end={v['end_seconds']}s")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                L.append(
                    f"- {src} `{v.get('url', '')}` at ({bb.get('x')}, {bb.get('y')}) "
                    f"size {bb.get('w')}×{bb.get('h')}{flag_str}"
                )
            L.append(
                "  - YouTube → `<Youtube id=\"...\" />` or an `<iframe>` to "
                "`https://www.youtube.com/embed/<id>`. "
                "Drive → `<iframe src=\"https://drive.google.com/file/d/<id>/preview\" allow=\"autoplay\" />`. "
                "Position the embed where the placeholder picture was."
            )

        shape_lines = _build_shape_lines(s)
        if shape_lines:
            L.append("")
            if (
                prev_shape_lines is not None
                and shape_lines == prev_shape_lines
                and prev_shape_idx is not None
            ):
                # Long decks repeat huge shape lists slide-to-slide; elide when
                # the geometry+text is identical to the previous slide and let
                # the diff block above carry the per-transition signal.
                L.append(
                    f"**Shapes (px in deck coords):** "
                    f"_(identical to slide {prev_shape_idx} — see above; the "
                    f"diff block above lists what changed at the run/format "
                    f"level)_"
                )
            else:
                L.append("**Shapes (px in deck coords):**")
                L.extend(shape_lines)
            prev_shape_lines = shape_lines
            prev_shape_idx = s["index"]

        cxns = s.get("connectors") or []
        if cxns:
            L.append("")
            L.append("**Connectors** (routing matches the source — paste the suggested `d` straight into an SVG `<path>`):")
            arrow_glyph = {"forward": "→", "reverse": "←", "both": "↔", "none": "—"}
            for c in cxns:
                st = c.get("start") or {}
                en = c.get("end") or {}
                glyph = arrow_glyph.get(c.get("arrow", "none"), "—")
                anchor_s = f"#{st['shape_id']} {st.get('site')}" if st.get("shape_id") else "free"
                anchor_e = f"#{en['shape_id']} {en.get('site')}" if en.get("shape_id") else "free"
                snap = "snapped" if c.get("snapped") else "loose"
                kind = c.get("kind", "?")
                d_attr = c.get("path") or ""
                s_id, e_id = st.get("shape_id"), en.get("shape_id")
                self_loop = bool(s_id and s_id == e_id)
                tags = []
                if self_loop:
                    tags.append("SELF-LOOP")
                if kind in ("bent4", "bent5"):
                    tags.append("MULTI-BEND")
                tag_str = f" **[{', '.join(tags)}]**" if tags else ""
                L.append(
                    f"- `{c.get('prst', '?')}` (kind={kind}, {snap}, arrow={c.get('arrow')}): {anchor_s} {glyph} {anchor_e}{tag_str}"
                )
                if (self_loop or kind in ("bent4", "bent5")) and st.get("site") and en.get("site"):
                    # Prefer the high-level spec form for these — `outset` plus
                    # snap refs survives box-position edits, raw `d` doesn't.
                    arrow = c.get("arrow", "forward")
                    arrow_field = "" if arrow == "forward" else f", \"arrow\": \"{arrow}\""
                    L.append(
                        f"  - spec form: `{{ \"from\": \"<id>.{st.get('site')}\", \"to\": \"<id>.{en.get('site')}\", \"outset\": 30{arrow_field} }}` "
                        f"(use real ids; tune `outset` to taste)"
                    )
                if d_attr:
                    L.append(f"  - `d=\"{d_attr}\"`")

        notes = s.get("notes") or ""
        if notes:
            L.append("")
            L.append("**Notes:**")
            for line in notes.split("\n"):
                L.append(f"> {line}")

        if not (text_paras or pics or shape_lines or cxns or notes or vids or tbls):
            L.append("")
            L.append("_(blank — likely a section divider)_")

        L.append("")

    # TOC: built last so it can read every annotation that the body emit pass
    # stashed on slide dicts (freeform, animations, scene_change, image_swap,
    # highlight_reveal, mermaid_hint).
    toc = ["## Contents", ""]
    for s in analysis["slides"]:
        title = _slide_one_liner(s)
        ann_tokens = _slide_toc_annotations(s)
        ann_str = f" — {' '.join(ann_tokens)}" if ann_tokens else ""
        toc.append(f"- **Slide {s['index']}**: {title}{ann_str}")
    toc.append("")

    final = preamble + toc + slide_body
    with open(path, "w") as f:
        f.write("\n".join(final))


def _adjust_template_paths(dest_dir, repo):
    """Rewrite `_shared/`-relative paths in the copied template for the
    destination's actual depth from the repo root.

    The template's `components/Diagram.vue` and `vite.config.ts` assume the
    talk dir sits one level below the repo root (`<repo>/<talk>/`). When a
    talk gets scaffolded somewhere deeper (e.g. `<repo>/tmp_talks/<talk>/`),
    `../../_shared/...` no longer resolves — we patch the references so they
    reach the actual `_shared/` location.
    """
    rel = os.path.relpath(dest_dir, repo)
    depth = len([p for p in rel.split(os.sep) if p and p != "."])
    if depth <= 1:
        return  # template was written for depth=1; nothing to adjust

    # components/Diagram.vue lives one level deeper than the talk dir, so the
    # import string needs (depth + 1) "../" segments to reach the repo root.
    diagram_vue = os.path.join(dest_dir, "components", "Diagram.vue")
    if os.path.isfile(diagram_vue):
        with open(diagram_vue) as f:
            content = f.read()
        new_rel = "/".join([".."] * (depth + 1)) + "/_shared/diagram/Diagram.vue"
        content = content.replace("../../_shared/diagram/Diagram.vue", new_rel)
        with open(diagram_vue, "w") as f:
            f.write(content)

    # vite.config.ts uses resolve(__dirname, '..') — needs `depth` "..` parts.
    vite_cfg = os.path.join(dest_dir, "vite.config.ts")
    if os.path.isfile(vite_cfg):
        with open(vite_cfg) as f:
            content = f.read()
        dots = ", ".join(["'..'"] * depth)
        content = content.replace("resolve(__dirname, '..')", f"resolve(__dirname, {dots})")
        with open(vite_cfg, "w") as f:
            f.write(content)

    # slides.md headmatter declares `theme: ../_shared/theme-josh` (depth=1).
    # Bump the prefix to match this deck's depth.
    slides_md = os.path.join(dest_dir, "slides.md")
    if os.path.isfile(slides_md):
        with open(slides_md) as f:
            content = f.read()
        new_prefix = "/".join([".."] * depth)
        content = content.replace(
            "theme: ../_shared/theme-josh",
            f"theme: {new_prefix}/_shared/theme-josh",
        )
        with open(slides_md, "w") as f:
            f.write(content)


def main():
    ap = argparse.ArgumentParser(description="Prep a PPTX for Slidev conversion.")
    ap.add_argument("pptx", help="Path to the .pptx file")
    ap.add_argument("--output", "-o", help="Destination dir name relative to --repo (default: slugified PPTX basename)")
    ap.add_argument("--repo", help="Repo root (default: cwd). Must contain a template/ dir.")
    ap.add_argument("--template", help="Override the template dir (default: <repo>/template)")
    args = ap.parse_args()

    pptx_path = os.path.abspath(args.pptx)
    if not os.path.isfile(pptx_path):
        sys.stderr.write(f"Error: PPTX not found: {pptx_path}\n")
        sys.exit(2)

    repo = os.path.abspath(args.repo or os.getcwd())
    template = os.path.abspath(args.template or os.path.join(repo, "template"))
    if not os.path.isdir(template):
        sys.stderr.write(f"Error: template dir not found: {template}\n")
        sys.stderr.write("Pass --template if it lives elsewhere.\n")
        sys.exit(2)

    dest_name = args.output or slugify(os.path.splitext(os.path.basename(pptx_path))[0]) or "talk"
    dest_dir = os.path.join(repo, dest_name)
    if os.path.exists(dest_dir):
        sys.stderr.write(f"Error: destination already exists: {dest_dir}\n")
        sys.stderr.write("Remove it or pass a different --output.\n")
        sys.exit(2)

    # template/ has a populated node_modules from the user's normal workflow;
    # copying it is slow (~500 MB) and corrupts the .bin/ symlinks, which then
    # breaks `npm run build`. Ignore it (and other generated dirs) and let the
    # user install fresh in the new talk dir.
    shutil.copytree(
        template, dest_dir,
        ignore=shutil.ignore_patterns(
            "node_modules", "dist", ".DS_Store", "package-lock.json",
        ),
    )
    _adjust_template_paths(dest_dir, repo)

    with zipfile.ZipFile(pptx_path) as zf:
        deck_w, deck_h = get_deck_size(parse_xml(zf, "ppt/presentation.xml"))

        slide_names = sorted(
            (n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
            key=lambda n: int(re.search(r"slide(\d+)\.xml$", n).group(1)),
        )

        # Extract every image from ppt/media/ into the talk dir
        media = [n for n in zf.namelist() if n.startswith("ppt/media/") and not n.endswith("/")]
        extracted_images = []
        for m in media:
            fname = os.path.basename(m)
            with zf.open(m) as src, open(os.path.join(dest_dir, fname), "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted_images.append(fname)

        videos_by_slide = load_videos_sidecar(pptx_path)
        thumbnails_by_slide = copy_thumbnails(pptx_path, dest_dir)
        slides = []
        for sname in slide_names:
            idx = int(re.search(r"slide(\d+)\.xml$", sname).group(1))
            rels_path = sname.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
            data = parse_slide(zf, sname, rels_path, deck_size=(deck_w, deck_h))
            data["notes"] = parse_notes(zf, f"ppt/notesSlides/notesSlide{idx}.xml")
            data["index"] = idx
            data["videos"] = videos_by_slide.get(idx, [])
            data["thumbnail"] = thumbnails_by_slide.get(idx)
            annotate_video_thumbnails(data)
            slides.append(data)

    analysis = {
        "pptx": os.path.basename(pptx_path),
        "deck_size": {"w": deck_w, "h": deck_h},
        "extracted_images": extracted_images,
        "thumbnails_dir": "./_thumbnails" if thumbnails_by_slide else None,
        "slides": slides,
    }
    json_path = os.path.join(dest_dir, "_analysis.json")
    md_path = os.path.join(dest_dir, "_analysis.md")
    # write_summary stashes derived fields (`freeform_figure`, `sliver_groups`,
    # `scene_change`) on each slide dict; emit the JSON afterwards so those
    # surface there too.
    write_summary(md_path, analysis)
    with open(json_path, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Scaffolded: {dest_dir}")
    print(f"  Slides parsed:    {len(slides)}")
    print(f"  Images extracted: {len(extracted_images)}")
    if thumbnails_by_slide:
        print(f"  Slide thumbnails: {len(thumbnails_by_slide)} (in ./_thumbnails/)")
    print(f"  Deck size:        {deck_w} × {deck_h} px")
    print(f"  Read next:        {os.path.relpath(md_path, os.getcwd())}")


if __name__ == "__main__":
    main()
