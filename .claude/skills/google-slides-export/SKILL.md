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

Run the bundled script:

```
python3 .claude/skills/google-slides-export/export.py <URL> --output <DIR> [--format pptx|pdf|odp|txt] [--recursive]
```

- `--output` / `-o`: destination directory (created if missing). Defaults to current directory.
- `--format` / `-f`: `pptx` (default), `pdf`, `odp`, `txt`.
- `--recursive` / `-r`: when the URL is a folder, recurse into subfolders. Off by default.

Pick the format from what the user asked for. If they did not specify, use `pptx`. Always ask the user where to save the output if they have not said so.

## First-run setup

The script needs an OAuth client and the Drive API enabled in a Google Cloud project. On first run it looks for `~/.config/google-slides-export/credentials.json`. If that file is missing it prints setup instructions and exits — relay them to the user verbatim. The summary:

1. In <https://console.cloud.google.com/> create or pick a project.
2. Enable the **Google Drive API** for that project.
3. Under **APIs & Services → Credentials**, create an **OAuth client ID** with application type **Desktop app**.
4. Download the client JSON and save it to `~/.config/google-slides-export/credentials.json`.
5. Add the Workspace user as a test user under **OAuth consent screen** (or publish the app).

On first run a browser window opens for the Google login + consent. The resulting token is cached at `~/.config/google-slides-export/token.json` and reused on subsequent runs (auto-refreshed when expired).

## Python dependencies

The script needs:

- `google-auth`
- `google-auth-oauthlib`
- `google-api-python-client`

If imports fail, install them (prefer a venv or `pipx`/`uv`, fall back to `pip install --user`):

```
pip install --user google-auth google-auth-oauthlib google-api-python-client
```

## Notes for the assistant

- Confirm the destination directory with the user before running if they have not specified one.
- Don't try to "fix" missing OAuth credentials yourself — surface the setup instructions and let the user complete them.
- The script exits non-zero on failure; surface stderr to the user.
- For folder URLs, only items with MIME type `application/vnd.google-apps.presentation` are exported; other files in the folder are skipped silently.
