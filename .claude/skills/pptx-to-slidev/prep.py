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
    """Yield (element, transform) for each sp / cxnSp / pic, applying any
    enclosing p:grpSp transforms so element bboxes can be mapped to slide-
    absolute coords."""
    def walk(parent, transform):
        for child in parent:
            tag = child.tag.split('}', 1)[-1]
            if tag == 'grpSp':
                new_t = _compose_transform(transform, _group_transform(child))
                yield from walk(child, new_t)
            elif tag in ('sp', 'cxnSp', 'pic'):
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
    xfrm = elem.find("p:spPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = elem.find("p:grpSpPr/a:xfrm", NS)
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


def _run_format(r):
    """Extract bold/italic/color from a run's rPr. None color = inherits default."""
    rpr = r.find("a:rPr", NS)
    bold = italic = False
    color = None
    if rpr is not None:
        bold = rpr.attrib.get("b") == "1"
        italic = rpr.attrib.get("i") == "1"
        clr = rpr.find(".//a:srgbClr", NS)
        if clr is not None:
            color = clr.attrib.get("val")
    return bold, italic, color


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
                bold, italic, color = _run_format(child)
                t = child.find("a:t", NS)
                text = (t.text or "") if t is not None else ""
                runs.append({"text": text, "bold": bold, "italic": italic, "color": color})
            elif tag == "fld":
                t = child.find("a:t", NS)
                text = (t.text or "") if t is not None else ""
                runs.append({"text": text, "bold": False, "italic": False, "color": None})
            elif tag == "br":
                runs.append({"text": "\n", "bold": False, "italic": False, "color": None})
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


def parse_slide(zf, slide_path, rels_path):
    root = parse_xml(zf, slide_path)
    if root is None:
        return {"error": f"could not parse {slide_path}"}

    shapes = []
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
            shape = {
                "id": sp_id,
                "name": name,
                "prst": prst,
                "bbox": apply_transform(get_xfrm(elem), transform),
                "text": extract_paragraphs(elem),
                "fill": _fill_color(spPr),
            }
            shapes.append(shape)
            if sp_id:
                shape_by_id[sp_id] = shape
        elif tag == 'cxnSp':
            deferred_connectors.append((elem, transform))
        elif tag == 'pic':
            deferred_pictures.append((elem, transform))

    connectors = []
    for cxn, transform in deferred_connectors:
        cnv = cxn.find("p:nvCxnSpPr/p:cNvPr", NS)
        name = cnv.attrib.get("name", "") if cnv is not None else ""
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
        blip = pic.find(".//a:blip", NS)
        rid = blip.attrib.get("{%s}embed" % NS["r"], "") if blip is not None else ""
        pictures.append({
            "name": name,
            "bbox": apply_transform(get_xfrm(pic), transform),
            "file": image_refs.get(rid),
        })

    return {
        "shapes": shapes,
        "connectors": connectors,
        "pictures": pictures,
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
    """Compact label describing a run's formatting deviations from the default."""
    parts = []
    if r.get("bold"):
        parts.append("b")
    if r.get("italic"):
        parts.append("i")
    if r.get("color"):
        parts.append("#" + r["color"])
    return "+".join(parts) if parts else "default"


def _is_formatted(r):
    return bool(r.get("bold") or r.get("italic") or r.get("color"))


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
    return (
        pic.get("file", ""),
        _round_pos(bb.get("x")), _round_pos(bb.get("y")),
        _round_pos(bb.get("w")), _round_pos(bb.get("h")),
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
    return f"`{pic.get('file', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}"


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

    L.append("")
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
        emit_list("added pictures", p_added, _picture_one_line)
    if p_removed:
        emit_list("removed pictures", p_removed, _picture_one_line)


def write_summary(path, analysis):
    L = []
    L.append(f"# PPTX analysis: {analysis['pptx']}")
    L.append("")
    sz = analysis["deck_size"]
    L.append(f"- Deck size: **{sz['w']} × {sz['h']} px** — use as SVG `viewBox` for diagram slides.")
    imgs = analysis["extracted_images"]
    L.append(f"- Extracted images (co-located with slides.md): {', '.join(f'`{n}`' for n in imgs) if imgs else '(none)'}")
    L.append(f"- Slide count: {len(analysis['slides'])}")
    L.append("")
    L.append("> Look for **adjacent slides with overlapping text/shapes** — they are almost always build-up animations to collapse into one Slidev slide with `v-click` reveals.")
    L.append(">")
    L.append("> **Each `**Diff from slide N**` block below is ONE click in the build-up.** If a diff lists five new shapes, all five share the same `revealAt`. Don't fragment a single source-slide transition across multiple clicks — the author chose to reveal those elements together for a reason (a node and its label, a binary op's two inputs, a structure and its annotation). Number clicks by source-slide transition, not by element count.")
    L.append(">")
    L.append("> A common variant: adjacent slides with **identical plain text but different run formatting** (bold/color shifts). That's a highlight-reveal build, not a duplicate. The script flags these inline as `⚠ HIGHLIGHT-REVEAL …`. Collapse them into one slide whose runs toggle their `.active` class based on `$clicks`.")
    L.append("")

    prev_plain = None
    prev_sig = None
    prev_index = None
    prev_slide = None
    if analysis.get("thumbnails_dir"):
        L.append(
            f"> 🖼  **Source thumbnails available**: every slide entry has a "
            f"`**Source:**` line pointing at a PNG render from "
            f"`{analysis['thumbnails_dir']}/`. **Read the PNG** before writing "
            f"the slide — it's the cheapest way to see what the original "
            f"actually looks like."
        )
        L.append("")

    for s in analysis["slides"]:
        L.append(f"## Slide {s['index']}")

        if s.get("thumbnail"):
            L.append("")
            L.append(f"**Source:** `{s['thumbnail']}` — read this PNG first.")

        plain = _slide_plain_text(s)
        sig = _slide_format_signature(s)
        if plain and plain == prev_plain and sig != prev_sig:
            L.append("")
            L.append(f"> ⚠ HIGHLIGHT-REVEAL: same plain text as slide {prev_index}, but per-run formatting differs. Collapse with slide {prev_index} into one Slidev slide where each segment toggles highlight on click.")
        prev_plain, prev_sig, prev_index = plain, sig, s["index"]

        mhint = _mermaidable(s)
        if mhint:
            L.append("")
            L.append(f"> 💡 Mermaid candidate ({mhint}): all shapes are basic and all connectors snap to them — consider a `mermaid` block instead of hand-rolled SVG. Skip if the diagram's spatial layout is itself meaningful.")

        _emit_diff(L, prev_slide, s)
        prev_slide = s

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
            for pic in pics:
                bb = pic.get("bbox") or {}
                placeholder_tag = (
                    "  ⚠ **video placeholder** — skip this picture and embed the matching video below instead"
                    if pic.get("video_placeholder") else ""
                )
                L.append(
                    f"- `{pic.get('file', '?')}` at ({bb.get('x')}, {bb.get('y')}) "
                    f"size {bb.get('w')}×{bb.get('h')}{placeholder_tag}"
                )

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

        shape_lines = []
        for sh in s.get("shapes", []):
            bb = sh.get("bbox") or {}
            if bb.get("x") is None:
                continue
            txt = " | ".join(p["text"] for p in sh.get("text", []))
            sid = sh.get("id")
            id_tag = f"#{sid} " if sid else ""
            fill_tag = f" fill={sh['fill']}" if sh.get("fill") else ""
            shape_lines.append(
                f"- {id_tag}`{sh.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}{fill_tag}  text={txt!r}"
            )
        if shape_lines:
            L.append("")
            L.append("**Shapes (px in deck coords):**")
            L.extend(shape_lines)

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

        if not (text_paras or pics or shape_lines or cxns or notes or vids):
            L.append("")
            L.append("_(blank — likely a section divider)_")

        L.append("")

    with open(path, "w") as f:
        f.write("\n".join(L))


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
            data = parse_slide(zf, sname, rels_path)
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
    with open(json_path, "w") as f:
        json.dump(analysis, f, indent=2)
    write_summary(md_path, analysis)

    print(f"Scaffolded: {dest_dir}")
    print(f"  Slides parsed:    {len(slides)}")
    print(f"  Images extracted: {len(extracted_images)}")
    if thumbnails_by_slide:
        print(f"  Slide thumbnails: {len(thumbnails_by_slide)} (in ./_thumbnails/)")
    print(f"  Deck size:        {deck_w} × {deck_h} px")
    print(f"  Read next:        {os.path.relpath(md_path, os.getcwd())}")


if __name__ == "__main__":
    main()
