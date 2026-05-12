#!/usr/bin/env python3
"""Export Google Slides presentations from a Drive folder or file URL."""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
except ImportError as e:
    sys.stderr.write(
        f"Missing Python dependency: {e.name}.\n"
        "Install with:\n"
        "  pip install --user google-auth google-auth-oauthlib google-api-python-client\n"
    )
    sys.exit(2)


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CONFIG_DIR = Path.home() / ".config" / "google-slides-export"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"

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
    file_id: str,
    file_name: str,
    mime_type: str,
    extension: str,
    out_dir: Path,
) -> Path:
    out_path = unique_path(out_dir / (safe_filename(file_name) + extension))
    request = service.files().export_media(fileId=file_id, mimeType=mime_type)
    with io.FileIO(out_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=4 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return out_path


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
                    service, f["id"], f["name"], mime_type, extension, out_dir,
                )
                print(f"  - {path}")
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
                service, meta["id"], meta["name"], mime_type, extension, out_dir,
            )
            print(f"Exported: {path}")
    except HttpError as e:
        sys.stderr.write(f"Google API error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
