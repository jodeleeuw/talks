#!/usr/bin/env python3
"""
pptx-to-slidev prep: scaffold a Slidev talk dir from a PPTX file and
emit a structured analysis Claude can read to write slides.md.

Stdlib only. Writes a new talk dir under <repo>/<output-name>/ containing:
  - the template's files (package.json, slides.md, .gitignore)
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


def get_xfrm(elem):
    xfrm = elem.find(".//a:xfrm", NS)
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


def _suggest_path(connector, bend_offset=80):
    """Synthesize an SVG `d` string that matches the source routing kind.

    Straight connectors → `L`. Bent connectors → orthogonal `H`/`V` segments
    (sharp 90° corners, like PowerPoint draws them). Curved connectors → a
    quadratic Bézier through the midpoint. Returns None when endpoints are
    unknown.
    """
    st = connector.get("start") or {}
    en = connector.get("end") or {}
    sx, sy, ex, ey = st.get("x"), st.get("y"), en.get("x"), en.get("y")
    if None in (sx, sy, ex, ey):
        return None

    kind = connector.get("kind", _classify_kind(connector.get("prst", "")))
    s_site = st.get("site")
    e_site = en.get("site")

    def fmt(n):
        # Trim trailing .0 for readability.
        return f"{n:g}"

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

    # Unknown bent shape (bent4/5, etc.) — straight-line fallback the user can
    # nudge by hand.
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
    for sp in root.iter("{%s}sp" % NS["p"]):
        cnv = sp.find("p:nvSpPr/p:cNvPr", NS)
        sp_id = cnv.attrib.get("id") if cnv is not None else None
        name = cnv.attrib.get("name", "") if cnv is not None else ""
        prst = ""
        spPr = sp.find("p:spPr", NS)
        if spPr is not None:
            prst_el = spPr.find("a:prstGeom", NS)
            if prst_el is not None:
                prst = prst_el.attrib.get("prst", "")
        shape = {
            "id": sp_id,
            "name": name,
            "prst": prst,
            "bbox": get_xfrm(sp),
            "text": extract_paragraphs(sp),
        }
        shapes.append(shape)
        if sp_id:
            shape_by_id[sp_id] = shape

    connectors = []
    for cxn in root.iter("{%s}cxnSp" % NS["p"]):
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
        bbox = get_xfrm(cxn)

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
    for pic in root.iter("{%s}pic" % NS["p"]):
        cnv = pic.find("p:nvPicPr/p:cNvPr", NS)
        name = cnv.attrib.get("name", "") if cnv is not None else ""
        blip = pic.find(".//a:blip", NS)
        rid = blip.attrib.get("{%s}embed" % NS["r"], "") if blip is not None else ""
        pictures.append({
            "name": name,
            "bbox": get_xfrm(pic),
            "file": image_refs.get(rid),
        })

    return {
        "shapes": shapes,
        "connectors": connectors,
        "pictures": pictures,
    }


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
    L.append("> A common variant: adjacent slides with **identical plain text but different run formatting** (bold/color shifts). That's a highlight-reveal build, not a duplicate. The script flags these inline as `⚠ HIGHLIGHT-REVEAL …`. Collapse them into one slide whose runs toggle their `.active` class based on `$clicks`.")
    L.append("")

    prev_plain = None
    prev_sig = None
    prev_index = None
    for s in analysis["slides"]:
        L.append(f"## Slide {s['index']}")

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
                L.append(f"- `{pic.get('file', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}")

        shape_lines = []
        for sh in s.get("shapes", []):
            bb = sh.get("bbox") or {}
            if bb.get("x") is None:
                continue
            txt = " | ".join(p["text"] for p in sh.get("text", []))
            sid = sh.get("id")
            id_tag = f"#{sid} " if sid else ""
            shape_lines.append(
                f"- {id_tag}`{sh.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}  text={txt!r}"
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
                L.append(
                    f"- `{c.get('prst', '?')}` (kind={kind}, {snap}, arrow={c.get('arrow')}): {anchor_s} {glyph} {anchor_e}"
                )
                if d_attr:
                    L.append(f"  - `d=\"{d_attr}\"`")

        notes = s.get("notes") or ""
        if notes:
            L.append("")
            L.append("**Notes:**")
            for line in notes.split("\n"):
                L.append(f"> {line}")

        if not (text_paras or pics or shape_lines or cxns or notes):
            L.append("")
            L.append("_(blank — likely a section divider)_")

        L.append("")

    with open(path, "w") as f:
        f.write("\n".join(L))


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

    shutil.copytree(template, dest_dir)

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

        slides = []
        for sname in slide_names:
            idx = int(re.search(r"slide(\d+)\.xml$", sname).group(1))
            rels_path = sname.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
            data = parse_slide(zf, sname, rels_path)
            data["notes"] = parse_notes(zf, f"ppt/notesSlides/notesSlide{idx}.xml")
            data["index"] = idx
            slides.append(data)

    analysis = {
        "pptx": os.path.basename(pptx_path),
        "deck_size": {"w": deck_w, "h": deck_h},
        "extracted_images": extracted_images,
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
    print(f"  Deck size:        {deck_w} × {deck_h} px")
    print(f"  Read next:        {os.path.relpath(md_path, os.getcwd())}")


if __name__ == "__main__":
    main()
