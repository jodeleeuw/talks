---
name: google-slides-export
description: Export Google Slides presentations from a Google Drive folder or file URL to a local directory. Uses browser-based OAuth against the user's Google Workspace account. Defaults to PPTX, but supports PDF, ODP, and TXT. Use when the user asks to download/export/fetch/grab a Google Slides deck (or all decks in a Drive folder) from a URL.
---

# Google Slides Export

Export Google Slides presentations from Google Drive to local files via the Drive API, authenticating through a browser OAuth flow.

## When to use

Invoke this skill whenever the user wants to download a Google Slides presentation, or all presentations in a Google Drive folder, given a URL. Accepts:

- Drive folder URLs: `https://drive.google.com/drive/folders/<ID>`
- Drive file URLs: `https://drive.google.com/file/d/<ID>/...`
- Slides URLs: `https://docs.google.com/presentation/d/<ID>/edit`
- `?id=<ID>` open URLs

## How to invoke

Run the bundled script via the repo's venv (see "Python dependencies" below):

```
.venv/bin/python .claude/skills/google-slides-export/export.py <URL> --output <DIR> [--format pptx|pdf|odp|txt] [--recursive]
```

- `--output` / `-o`: destination directory (created if missing). Defaults to current directory.
- `--format` / `-f`: `pptx` (default), `pdf`, `odp`, `txt`.
- `--recursive` / `-r`: when the URL is a folder, recurse into subfolders. Off by default.

Pick the format from what the user asked for. If they did not specify, use `pptx`. Always ask the user where to save the output if they have not said so.

## First-run setup

The script needs an OAuth client and **both the Drive API and the Slides API** enabled in a Google Cloud project. On first run it looks for `~/.config/google-slides-export/credentials.json`. If that file is missing it prints setup instructions and exits — relay them to the user verbatim. The summary:

1. In <https://console.cloud.google.com/> create or pick a project.
2. Enable the **Google Drive API** and the **Google Slides API** for that project.
3. Under **APIs & Services → Credentials**, create an **OAuth client ID** with application type **Desktop app**.
4. Download the client JSON and save it to `~/.config/google-slides-export/credentials.json`.
5. Add the Workspace user as a test user under **OAuth consent screen** (or publish the app).

On first run a browser window opens for the Google login + consent. The resulting token is cached at `~/.config/google-slides-export/token.json` and reused on subsequent runs (auto-refreshed when expired).

### Re-consent when scopes change

If you've used a previous version of this skill, your cached token only has the `drive.readonly` scope and won't satisfy the new `presentations.readonly` requirement. The script detects this on launch and forces a fresh browser consent — no manual cleanup needed. If you ever want to wipe the token by hand, delete `~/.config/google-slides-export/token.json`.

## Python dependencies

The script needs:

- `google-auth`
- `google-auth-oauthlib`
- `google-api-python-client`

This repo expects a venv at the repo root (`.venv/`, gitignored). On macOS with Homebrew Python, plain `pip install --user` is blocked by PEP 668, and `pipx` targets applications rather than libraries, so a project-local venv is the right path. Create it once:

```
python3 -m venv .venv
.venv/bin/pip install google-auth google-auth-oauthlib google-api-python-client
```

Then invoke the script via `.venv/bin/python` (see "How to invoke" above). The script's import-error message also surfaces this recipe.

## Video sidecar (`<deck>.videos.json`)

Google's PPTX export silently replaces every embedded video — YouTube and Drive alike — with a static thumbnail PNG. The video URL, source, and playback settings are dropped. When `--format pptx`, the script runs a second pass against the **Slides API** to recover that metadata and writes it to a sidecar next to the PPTX:

```
<deck>.pptx
<deck>.videos.json   # only created if the deck has at least one video
```

The sidecar shape:

```json
{
  "presentation_id": "1AbC...",
  "slides": [
    {
      "index": 19,
      "videos": [
        {
          "source": "YOUTUBE",
          "id": "abc123",
          "url": "https://www.youtube.com/watch?v=abc123",
          "bbox": {"x": 353.1, "y": 143.1, "w": 253.8, "h": 253.8},
          "autoplay": false,
          "start_seconds": null,
          "end_seconds": null,
          "mute": false
        }
      ]
    }
  ]
}
```

`index` is 1-based, matching `ppt/slides/slideN.xml`. `bbox` is in deck pixels (EMU/9525). `pptx-to-slidev`'s `prep.py` reads this file automatically if it sits next to the PPTX. Other formats (pdf/odp/txt) don't generate a sidecar — they aren't fed into the Slidev pipeline.

If the Slides API call fails (deleted file, scope denied, etc.) the script logs a warning to stderr and continues — the PPTX export still succeeds.

## Large decks (10 MB export cap)

The Drive API's `files.export` endpoint rejects files larger than ~10 MB with `exportSizeLimitExceeded` ("This file is too large to be exported."). Image-heavy decks hit this easily.

The script handles this automatically: when `files.export` returns the size-limit error, it falls back to `https://docs.google.com/presentation/d/<ID>/export/<fmt>` — the same undocumented endpoint the Slides web UI uses for File → Download. This endpoint enforces no size cap and accepts the same OAuth bearer token. You'll see `Drive export hit the 10MB cap; retrying via docs.google.com.` on stderr when this kicks in.

If the fallback ever stops working (Google could change the endpoint), the last-resort path is asking the user to download manually via File → Download → Microsoft PowerPoint in the Slides UI.

## Notes for the assistant

- Confirm the destination directory with the user before running if they have not specified one.
- Don't try to "fix" missing OAuth credentials yourself — surface the setup instructions and let the user complete them.
- The script exits non-zero on failure; surface stderr to the user.
- For folder URLs, only items with MIME type `application/vnd.google-apps.presentation` are exported; other files in the folder are skipped silently.
