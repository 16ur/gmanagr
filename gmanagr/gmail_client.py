import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmanagr.models import Email


class GmailClient:
    def __init__(self, creds):
        self.service = build("gmail", "v1", credentials=creds)

    def get_labels(self):
        labels = self.service.users().labels().list(userId="me").execute()
        return [item for item in labels.get("labels", []) if item["type"] == "user"]

    def get_messages(self, days: int) -> list[Email]:
        after = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
        result = self.service.users().messages().list(userId="me", q=f"after:{after} in:inbox").execute()
        mails = []
        for msg in result.get("messages", []):
            response = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            headers = response["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No subject")
            from_raw = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            date_raw = next((h["value"] for h in headers if h["name"] == "Date"), "No date")
            local_time = parsedate_to_datetime(date_raw).astimezone().strftime("%Y-%m-%d %H:%M")
            mails.append(Email(
                id=response["id"],
                subject=subject,
                from_raw=from_raw,
                date=local_time,
                is_unread="UNREAD" in response["labelIds"],
            ))
        return mails

    def create_label(self, name: str):
        return self.service.users().labels().create(userId="me", body={"name": name}).execute()

    def trash_message(self, mail_id: str):
        return self.service.users().messages().trash(userId="me", id=mail_id).execute()

    def apply_label(self, mail_id: str, label_id: str):
        return (
            self.service.users()
            .messages()
            .modify(userId="me", id=mail_id, body={"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]})
            .execute()
        )

    def create_filter(self, sender_email: str, label_id: str):
        body = {
            "criteria": {"from": sender_email},
            "action": {"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]},
        }
        try:
            return (
                self.service.users().settings().filters().create(userId="me", body=body).execute()
            )
        except HttpError as e:
            if e.status_code == 400:
                return None
            raise

    def get_from_email(self, from_raw: str) -> str:
        match = re.search(r"<(.+?)>", from_raw)
        return match.group(1) if match else from_raw
