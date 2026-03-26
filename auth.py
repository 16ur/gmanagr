import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os


def getCredentials(credsPath):
    return InstalledAppFlow.from_client_secrets_file(
        credsPath,
        scopes=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.settings.basic",
        ],
    )

def checkToken():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = getCredentials("credentials.json")
            creds = flow.run_local_server()
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return creds
    