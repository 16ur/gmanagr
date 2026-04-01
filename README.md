# gmanagr

A terminal-based Gmail manager built with Python and Textual. Browse your recent emails, create labels, and set up automatic filters, all from your terminal.

## Features

- Browse emails from the last N days
- Apply labels to emails with a single keypress
- Automatically create a Gmail filter for the sender so future emails are sorted too
- Create new labels on the fly from the interface
- Persistent OAuth2 authentication (no need to log in every time)

## Tech Stack

- **[Textual](https://textual.textualize.io/)** — TUI framework
- **[Google Gmail API](https://developers.google.com/gmail/api)** — Gmail integration
- **[uv](https://docs.astral.sh/uv/)** — Python package manager

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
git clone https://github.com/your-username/gmanagr
cd gmanagr

uv sync
```

## Usage

```bash
uv run main.py
```

On first launch, a browser window will open for OAuth2 authentication. After that, the token is cached locally and you won't need to authenticate again.
