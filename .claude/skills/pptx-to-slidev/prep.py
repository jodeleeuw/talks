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


def extract_paragraphs(elem):
    """Return [{text, level}] for each non-empty paragraph under elem."""
    out = []
    for p in elem.iter("{%s}p" % NS["a"]):
        text = "".join((t.text or "") for t in p.iter("{%s}t" % NS["a"]))
        if not text.strip():
            continue
        level = 0
        pPr = p.find("a:pPr", NS)
        if pPr is not None and pPr.attrib.get("lvl"):
            try:
                level = int(pPr.attrib["lvl"])
            except ValueError:
                pass
        out.append({"text": text, "level": level})
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


def parse_slide(zf, slide_path, rels_path):
    root = parse_xml(zf, slide_path)
    if root is None:
        return {"error": f"could not parse {slide_path}"}

    shapes = []
    for sp in root.iter("{%s}sp" % NS["p"]):
        cnv = sp.find("p:nvSpPr/p:cNvPr", NS)
        name = cnv.attrib.get("name", "") if cnv is not None else ""
        prst = ""
        spPr = sp.find("p:spPr", NS)
        if spPr is not None:
            prst_el = spPr.find("a:prstGeom", NS)
            if prst_el is not None:
                prst = prst_el.attrib.get("prst", "")
        shapes.append({
            "name": name,
            "prst": prst,
            "bbox": get_xfrm(sp),
            "text": extract_paragraphs(sp),
        })

    connectors = []
    for cxn in root.iter("{%s}cxnSp" % NS["p"]):
        cnv = cxn.find("p:nvCxnSpPr/p:cNvPr", NS)
        name = cnv.attrib.get("name", "") if cnv is not None else ""
        prst = ""
        spPr = cxn.find("p:spPr", NS)
        if spPr is not None:
            prst_el = spPr.find("a:prstGeom", NS)
            if prst_el is not None:
                prst = prst_el.attrib.get("prst", "")
        connectors.append({
            "name": name,
            "prst": prst,
            "bbox": get_xfrm(cxn),
        })

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
    L.append("")
    for s in analysis["slides"]:
        L.append(f"## Slide {s['index']}")

        # Text paragraphs across all shapes
        text_paras = []
        for sh in s.get("shapes", []):
            for p in sh.get("text", []):
                text_paras.append((p["level"], p["text"]))
        if text_paras:
            L.append("")
            L.append("**Text:**")
            for level, text in text_paras:
                L.append(f"{'  ' * level}- {text}")

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
            shape_lines.append(
                f"- `{sh.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}  text={txt!r}"
            )
        if shape_lines:
            L.append("")
            L.append("**Shapes (px in deck coords):**")
            L.extend(shape_lines)

        cxns = s.get("connectors") or []
        if cxns:
            L.append("")
            L.append("**Connectors:**")
            for c in cxns:
                bb = c.get("bbox") or {}
                flips = []
                if bb.get("flipH"):
                    flips.append("flipH")
                if bb.get("flipV"):
                    flips.append("flipV")
                fs = " " + "+".join(flips) if flips else ""
                L.append(
                    f"- `{c.get('prst', '?')}` at ({bb.get('x')}, {bb.get('y')}) size {bb.get('w')}×{bb.get('h')}{fs}"
                )

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
