from googleapiclient.discovery import build
from auth import checkToken
from datetime import datetime, timedelta


class GmailClient:
    def __init__(self, creds):
        self.creds = creds
        self.service = build("gmail", "v1", credentials=creds)

    def getLabels(self):
        labels = self.service.users().labels().list(userId="me").execute()
        return [item for item in labels.get("labels", []) if item["type"] == "user"]

    def getMessages(self, days):
        after = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
        q = f"after:{after}"
        labels = self.service.users().messages().list(userId="me", q=q).execute()
        return labels


creds = checkToken()

client = GmailClient(creds)

print(client.getMessages(days=2))
