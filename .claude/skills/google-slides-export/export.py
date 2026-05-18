#!/usr/bin/env python3
"""Export Google Slides presentations from a Drive folder or file URL."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

try:
    from google.auth.transport.requests import AuthorizedSession, Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
except ImportError as e:
    sys.stderr.write(
        f"Missing Python dependency: {e.name}.\n"
        "This repo expects a venv at the repo root. Create and populate it with:\n"
        "  python3 -m venv .venv\n"
        "  .venv/bin/pip install google-auth google-auth-oauthlib google-api-python-client\n"
        "Then re-run via:\n"
        "  .venv/bin/python .claude/skills/google-slides-export/export.py ...\n"
    )
    sys.exit(2)


SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    # Needed to fetch video element metadata that PPTX export drops on the
    # floor (videos become static thumbnails in the .pptx). See
    # fetch_videos_sidecar.
    "https://www.googleapis.com/auth/presentations.readonly",
]
CONFIG_DIR = Path.home() / ".config" / "google-slides-export"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"

EMU_PER_PX = 9525

SLIDES_MIME = "application/vnd.google-apps.presentation"
FOLDER_MIME = "application/vnd.google-apps.folder"

FORMATS: dict[str, tuple[str, str]] = {
    "pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
    "pdf": ("application/pdf", ".pdf"),
    "odp": ("application/vnd.oasis.opendocument.presentation", ".odp"),
    "txt": ("text/plain", ".txt"),
}

SETUP_INSTRUCTIONS = f"""\
No OAuth client credentials found at {CREDENTIALS_PATH}.

One-time setup:
  1. Open https://console.cloud.google.com/ and create or select a project.
  2. Enable the "Google Drive API" for that project.
  3. Under "APIs & Services" -> "Credentials", click
     "Create credentials" -> "OAuth client ID".
  4. Choose application type "Desktop app" and create it.
  5. Download the client JSON and save it to:
       {CREDENTIALS_PATH}
  6. Under "OAuth consent screen", add your Workspace email as a test user
     (or publish the app).

Then re-run this command. A browser window will open for Google sign-in.
"""


def get_credentials() -> Credentials:
    creds: Credentials | None = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    # `creds.valid` checks expiry but not scopes, so a token saved before we
    # added the presentations scope would slip through and then 403 on the
    # Slides API. Force re-consent when the cached scopes are insufficient.
    if creds and not _has_required_scopes(creds):
        sys.stderr.write(
            "Cached token is missing newly-required scopes; re-authenticating.\n"
        )
        creds = None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception as e:
            sys.stderr.write(f"Token refresh failed ({e}); re-authenticating.\n")
            creds = None
    if not CREDENTIALS_PATH.exists():
        sys.stderr.write(SETUP_INSTRUCTIONS)
        sys.exit(1)
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        authorization_prompt_message=(
            "A browser window will open for Google sign-in. "
            "If it does not, visit this URL: {url}"
        ),
        success_message="Authentication complete. You can close this tab.",
    )
    _save_token(creds)
    return creds


def _has_required_scopes(creds: Credentials) -> bool:
    """True if cached creds cover every scope we now require."""
    granted = set(creds.scopes or [])
    return all(s in granted for s in SCOPES)


def _save_token(creds: Credentials) -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    try:
        TOKEN_PATH.chmod(0o600)
    except OSError:
        pass


def parse_url(url: str) -> tuple[str, str]:
    """Return (kind, id) where kind is 'folder' or 'file'."""
    m = re.search(r"/folders/([A-Za-z0-9_-]+)", url)
    if m:
        return "folder", m.group(1)
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    if m:
        return "file", m.group(1)
    m = re.search(r"[?&]id=([A-Za-z0-9_-]+)", url)
    if m:
        return "file", m.group(1)
    sys.stderr.write(f"Could not parse a Drive folder or file ID from URL: {url}\n")
    sys.exit(1)


def safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip().rstrip(".")
    return name or "presentation"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 2
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def list_presentations(service, folder_id: str, recursive: bool) -> list[dict]:
    presentations: list[dict] = []
    stack = [folder_id]
    visited: set[str] = set()
    while stack:
        fid = stack.pop()
        if fid in visited:
            continue
        visited.add(fid)
        page_token: str | None = None
        while True:
            resp = service.files().list(
                q=f"'{fid}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000,
            ).execute()
            for f in resp.get("files", []):
                if f["mimeType"] == SLIDES_MIME:
                    presentations.append(f)
                elif recursive and f["mimeType"] == FOLDER_MIME:
                    stack.append(f["id"])
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    return presentations


def export_file(
    service,
    creds: Credentials,
    file_id: str,
    file_name: str,
    fmt: str,
    mime_type: str,
    extension: str,
    out_dir: Path,
) -> Path:
    out_path = unique_path(out_dir / (safe_filename(file_name) + extension))
    request = service.files().export_media(fileId=file_id, mimeType=mime_type)
    try:
        with io.FileIO(out_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=4 * 1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return out_path
    except HttpError as e:
        # FileIO already created an empty file; clean it up on every failure
        # path so the directory is not left littered with 0-byte placeholders.
        try:
            out_path.unlink()
        except FileNotFoundError:
            pass
        # Drive API caps export at ~10MB. The docs.google.com UI export endpoint
        # has no such cap, so fall back to it for size-limit failures.
        if _is_export_size_limit(e):
            sys.stderr.write(
                "Drive export hit the 10MB cap; retrying via docs.google.com.\n"
            )
            return _export_via_docs_endpoint(
                creds, file_id, file_name, fmt, extension, out_dir,
            )
        raise


def _is_export_size_limit(e: HttpError) -> bool:
    if getattr(e, "status_code", None) == 403 or e.resp.status == 403:
        return b"exportSizeLimitExceeded" in (e.content or b"")
    return False


# Path component for the docs.google.com export endpoint.
DOCS_EXPORT_PATH: dict[str, str] = {
    "pptx": "pptx",
    "pdf": "pdf",
    "odp": "odp",
    "txt": "txt",
}


def _export_via_docs_endpoint(
    creds: Credentials,
    file_id: str,
    file_name: str,
    fmt: str,
    extension: str,
    out_dir: Path,
) -> Path:
    out_path = unique_path(out_dir / (safe_filename(file_name) + extension))
    session = AuthorizedSession(creds)
    url = (
        f"https://docs.google.com/presentation/d/{file_id}/export/"
        f"{DOCS_EXPORT_PATH[fmt]}?id={file_id}"
    )
    with session.get(url, stream=True, allow_redirects=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError(
                f"docs.google.com export returned HTTP {resp.status_code}: "
                f"{resp.text[:300]}"
            )
        with io.FileIO(out_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
    return out_path


def _iter_page_elements(elements):
    """Yield every leaf pageElement, recursing into elementGroup children.

    The Slides API nests grouped elements under `elementGroup.children`, and
    groups can themselves contain groups. A flat walk would miss any video
    placed inside a group.
    """
    for e in elements or []:
        if "elementGroup" in e:
            yield from _iter_page_elements(
                (e.get("elementGroup") or {}).get("children", [])
            )
        else:
            yield e


def _element_bbox_px(elem: dict) -> dict | None:
    """Compute a slide-absolute bbox in px from a PageElement's size/transform.

    Slides API gives `size.{width,height}.magnitude` in EMU and a `transform`
    with `scaleX/scaleY/translateX/translateY` (also EMU when unit=EMU). The
    visual extent is `(translateX, translateY, scaleX * width, scaleY * height)`.
    Returns None when size data is missing.
    """
    size = elem.get("size") or {}
    w_emu = ((size.get("width") or {}).get("magnitude")) or 0
    h_emu = ((size.get("height") or {}).get("magnitude")) or 0
    if not (w_emu or h_emu):
        return None
    tr = elem.get("transform") or {}
    sx = tr.get("scaleX", 1) or 0
    sy = tr.get("scaleY", 1) or 0
    tx = tr.get("translateX", 0) or 0
    ty = tr.get("translateY", 0) or 0
    return {
        "x": round(tx / EMU_PER_PX, 1),
        "y": round(ty / EMU_PER_PX, 1),
        "w": round(sx * w_emu / EMU_PER_PX, 1),
        "h": round(sy * h_emu / EMU_PER_PX, 1),
    }


def fetch_videos_sidecar(creds: Credentials, presentation_id: str) -> dict:
    """Return a sidecar dict listing every video page-element per slide.

    Google's PPTX export silently replaces video elements with a static
    thumbnail image — the URL, source (YouTube/Drive), and playback settings
    are dropped. We query the Slides API to recover them so prep.py can hint
    the conversion. Slide indices are 1-based to match `ppt/slides/slideN.xml`.
    """
    slides_service = build(
        "slides", "v1", credentials=creds, cache_discovery=False,
    )
    pres = slides_service.presentations().get(
        presentationId=presentation_id,
    ).execute()
    out_slides: list[dict] = []
    for idx, slide in enumerate(pres.get("slides", []) or [], start=1):
        videos: list[dict] = []
        for elem in _iter_page_elements(slide.get("pageElements", [])):
            v = elem.get("video")
            if not v:
                continue
            vp = v.get("videoProperties") or {}
            videos.append({
                "source": v.get("source"),
                "id": v.get("id"),
                "url": v.get("url"),
                "bbox": _element_bbox_px(elem),
                "autoplay": vp.get("autoPlay", False),
                "start_seconds": vp.get("start"),
                "end_seconds": vp.get("end"),
                "mute": vp.get("mute", False),
            })
        if videos:
            out_slides.append({"index": idx, "videos": videos})
    return {"presentation_id": presentation_id, "slides": out_slides}


def write_videos_sidecar(
    creds: Credentials, file_id: str, pptx_path: Path,
) -> Path | None:
    """Fetch videos for `file_id` and write `<pptx_stem>.videos.json` beside
    the PPTX. Returns the sidecar path if anything was written, else None."""
    try:
        sidecar = fetch_videos_sidecar(creds, file_id)
    except HttpError as e:
        sys.stderr.write(
            f"Could not fetch video metadata for {pptx_path.name} "
            f"({e}); skipping sidecar.\n"
        )
        return None
    if not sidecar.get("slides"):
        return None
    sidecar_path = pptx_path.with_suffix(".videos.json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    return sidecar_path


def fetch_thumbnails(
    creds: Credentials,
    presentation_id: str,
    out_dir: Path,
    size: str = "LARGE",
) -> list[tuple[int, Path]]:
    """Render each slide to PNG via the Slides API.

    For each slide we call `presentations.pages.getThumbnail`, which returns a
    short-lived signed contentUrl. The PNG is then fetched over plain HTTPS
    (no auth needed for the download itself). PNGs land as
    `<out_dir>/slide-<N>.png` with N 1-based to match `ppt/slides/slideN.xml`.

    Returns a list of (slide_index, path) tuples for every PNG written.
    """
    slides_service = build(
        "slides", "v1", credentials=creds, cache_discovery=False,
    )
    pres = slides_service.presentations().get(
        presentationId=presentation_id,
        fields="slides(objectId)",
    ).execute()
    slides = pres.get("slides", []) or []
    if not slides:
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[tuple[int, Path]] = []
    # Plain HTTP session is fine — contentUrl is a signed URL with its own auth.
    import urllib.request
    for idx, slide in enumerate(slides, start=1):
        page_id = slide.get("objectId")
        if not page_id:
            continue
        try:
            thumb = slides_service.presentations().pages().getThumbnail(
                presentationId=presentation_id,
                pageObjectId=page_id,
                thumbnailProperties_thumbnailSize=size,
            ).execute()
        except HttpError as e:
            sys.stderr.write(
                f"  thumbnail slide {idx}: API error {e}; skipping.\n"
            )
            continue
        url = (thumb or {}).get("contentUrl")
        if not url:
            continue
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
        except Exception as e:
            sys.stderr.write(
                f"  thumbnail slide {idx}: download failed ({e}); skipping.\n"
            )
            continue
        path = out_dir / f"slide-{idx}.png"
        path.write_bytes(data)
        saved.append((idx, path))
    return saved


def write_thumbnails(
    creds: Credentials,
    file_id: str,
    pptx_path: Path,
    size: str = "LARGE",
) -> Path | None:
    """Fetch slide PNGs for `file_id` into `<pptx_stem>.thumbnails/`.

    Returns the thumbnails directory if anything was written, else None.
    Existing directories with the expected name are skipped (no clobber).
    """
    thumbs_dir = pptx_path.with_suffix(".thumbnails")
    if thumbs_dir.exists() and any(thumbs_dir.iterdir()):
        return thumbs_dir
    try:
        saved = fetch_thumbnails(creds, file_id, thumbs_dir, size=size)
    except HttpError as e:
        sys.stderr.write(
            f"Could not fetch slide thumbnails for {pptx_path.name} "
            f"({e}); skipping.\n"
        )
        return None
    if not saved:
        # Clean up the empty dir we created
        try:
            thumbs_dir.rmdir()
        except OSError:
            pass
        return None
    return thumbs_dir


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Export Google Slides presentations from a Drive URL.",
    )
    ap.add_argument("url", help="Drive folder URL, file URL, or Slides URL")
    ap.add_argument(
        "-o", "--output", default=".",
        help="Output directory (default: current directory)",
    )
    ap.add_argument(
        "-f", "--format", default="pptx", choices=sorted(FORMATS.keys()),
        help="Export format (default: pptx)",
    )
    ap.add_argument(
        "-r", "--recursive", action="store_true",
        help="Recurse into subfolders when URL is a folder",
    )
    ap.add_argument(
        "--no-thumbnails", action="store_true",
        help=(
            "Skip per-slide PNG thumbnails (only meaningful with --format pptx). "
            "Thumbnails are rendered server-side via the Slides API and saved "
            "to <pptx_stem>.thumbnails/slide-N.png; pptx-to-slidev surfaces "
            "them in the analysis so Claude can see each source slide."
        ),
    )
    ap.add_argument(
        "--thumbnail-size", default="LARGE",
        choices=("SMALL", "MEDIUM", "LARGE"),
        help="Thumbnail size for --thumbnails (default: LARGE).",
    )
    args = ap.parse_args()

    mime_type, extension = FORMATS[args.format]
    out_dir = Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    kind, fid = parse_url(args.url)

    try:
        if kind == "folder":
            files = list_presentations(service, fid, recursive=args.recursive)
            if not files:
                print(f"No Google Slides presentations found in folder {fid}.")
                return
            print(f"Found {len(files)} presentation(s). Exporting to {out_dir}")
            for f in files:
                path = export_file(
                    service, creds, f["id"], f["name"],
                    args.format, mime_type, extension, out_dir,
                )
                print(f"  - {path}")
                if args.format == "pptx":
                    sidecar = write_videos_sidecar(creds, f["id"], path)
                    if sidecar:
                        print(f"    + {sidecar.name} (video metadata)")
                    if not args.no_thumbnails:
                        thumbs = write_thumbnails(
                            creds, f["id"], path, size=args.thumbnail_size,
                        )
                        if thumbs:
                            count = sum(1 for _ in thumbs.iterdir())
                            print(f"    + {thumbs.name}/ ({count} slide PNGs)")
        else:
            meta = service.files().get(
                fileId=fid,
                fields="id, name, mimeType",
                supportsAllDrives=True,
            ).execute()
            if meta["mimeType"] != SLIDES_MIME:
                sys.stderr.write(
                    f"File '{meta['name']}' is not a Google Slides presentation "
                    f"(mimeType: {meta['mimeType']}).\n"
                )
                sys.exit(1)
            path = export_file(
                service, creds, meta["id"], meta["name"],
                args.format, mime_type, extension, out_dir,
            )
            print(f"Exported: {path}")
            if args.format == "pptx":
                sidecar = write_videos_sidecar(creds, meta["id"], path)
                if sidecar:
                    print(f"  + {sidecar.name} (video metadata)")
                if not args.no_thumbnails:
                    thumbs = write_thumbnails(
                        creds, meta["id"], path, size=args.thumbnail_size,
                    )
                    if thumbs:
                        count = sum(1 for _ in thumbs.iterdir())
                        print(f"  + {thumbs.name}/ ({count} slide PNGs)")
    except HttpError as e:
        sys.stderr.write(f"Google API error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
