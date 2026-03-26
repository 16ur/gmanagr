import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
import os


def getCredentials(credsPath):
    return InstalledAppFlow.from_client_secrets_file(
        credsPath,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.settings.basic",
        ],
    )

def checkToken():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    else:
        flow = getCredentials("credentials.json")
        creds = flow.run_local_server()
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    

checkToken()