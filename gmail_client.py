from googleapiclient.discovery import build
from auth import checkToken
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Email:
    id: str
    subject: str
    from_raw: str
    date: str
    is_unread: bool


class GmailClient:
    def __init__(self, creds):
        self.creds = creds
        self.service = build("gmail", "v1", credentials=creds)

    def get_labels(self):
        labels = self.service.users().labels().list(userId="me").execute()
        return [item for item in labels.get("labels", []) if item["type"] == "user"]

    def get_messages(self, days):
        after = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
        q = f"after:{after}"
        labels = self.service.users().messages().list(userId="me", q=q).execute()

        mails_ids = [label["id"] for label in labels.get("messages", [])]

        mails = []
        for mail_id in mails_ids:
            response = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=mail_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )

            headers = response["payload"]["headers"]
            mail_id = response["id"]
            subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"), "No subject"
            )
            from_raw = next(
                (h["value"] for h in headers if h["name"] == "From"), "Unknown"
            )
            date_raw = next(h["value"] for h in headers if h["name"] == "Date")

            labels_value = response["labelIds"]
            is_unread = "UNREAD" in labels_value

            email = Email(
                id=mail_id,
                subject=subject,
                from_raw=from_raw,
                date=date_raw,
                is_unread=is_unread,
            )
            mails.append(email)
        return mails
            
    def create_label(self, name):
        body = {"name": name}
        response = self.service.users().labels().create(userId="me", body=body).execute()
        return response 

creds = checkToken()
client = GmailClient(creds)
# print(client.get_messages(days=1))
client.create_label("Label Test")
