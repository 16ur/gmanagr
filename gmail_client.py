from googleapiclient.discovery import build
from auth import checkToken

class GmailClient:
    def __init__(self, creds):
        self.creds = creds
        self.service = build("gmail", "v1", credentials = creds)
    
    def getLabels(self):
        labels = self.service.users().labels().list(userId="me").execute()
        return [item for item in labels.get("labels",[]) if item["type"] == "user"]
        
creds = checkToken()
client = GmailClient(creds)
print(client.getLabels())
