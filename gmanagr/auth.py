import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

_PROJECT_ROOT = Path(__file__).parent.parent
_CREDENTIALS_PATH = _PROJECT_ROOT / "credentials.json"
_TOKEN_PATH = _PROJECT_ROOT / "token.pickle"

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]


def check_token():
    creds = None
    if _TOKEN_PATH.exists():
        with open(_TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(_CREDENTIALS_PATH, _SCOPES)
            creds = flow.run_local_server()
        with open(_TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return creds
