# gmanagr

A keyboard-driven Gmail manager for the terminal.

## Features

- Browse inbox emails from the last N days (2 by default)
- Apply labels to emails with a single keypress
- Batch-apply labels to all inbox emails from the same sender at once
- Automatically create a Gmail filter for the sender so future emails are sorted too
- Create new labels on the fly from the label picker
- Move emails to trash with a confirmation prompt

## Keybindings

| Key | Action |
|-----|--------|
| `x` | Apply a label to the selected email |
| `backspace` | Move the selected email to trash |
| `t` | Change the time range |
| `d` | Toggle theme |
| `esc` | Close a modal |

## Tech Stack

- **[Python 3.12](https://www.python.org/)**
- **[Textual](https://textual.textualize.io/)** — TUI framework
- **[Google Gmail API](https://developers.google.com/gmail/api)** — Gmail integration
- **[uv](https://docs.astral.sh/uv/)** — package manager

## Prerequisites

- Python 3.12+
- A Google Cloud project with the Gmail API enabled
- OAuth2 credentials (`credentials.json`)

## Google Cloud Setup

This only needs to be done once.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable the **Gmail API** — APIs & Services → Library → Gmail API → Enable
4. Configure the OAuth consent screen — APIs & Services → OAuth consent screen
   - Choose **External**, fill in the app name and your email
   - Add your Gmail address as a **Test user**
5. Create OAuth credentials — APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Download the JSON file and rename it `credentials.json`
   - Place it at the root of the project

## Installation

```bash
git clone https://github.com/16ur/gmanagr
cd gmanagr
uv sync
```

## Usage

```bash
uv run main.py
```

On first launch, a browser window will open for OAuth2 authentication. After that, the token is cached locally and re-used automatically.
