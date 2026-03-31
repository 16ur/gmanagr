from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dataclasses import dataclass


def parse_date(date_raw: str) -> str:
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",   # +0000
        "%a, %d %b %Y %H:%M:%S %Z",   # GMT, UTC, etc..
        "%d %b %Y %H:%M:%S %z",       # without day
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_raw, fmt).strftime("%d %b %H:%M")
        except ValueError:
            continue
    return date_raw[:16]

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
        q = f"after:{after} in:inbox"
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
            date_raw = next(
                (h["value"] for h in headers if h["name"] == "Date"), "No date"
            )
            
            # Format the date
            date_formatted = parse_date(date_raw)
            
            labels_value = response["labelIds"]
            is_unread = "UNREAD" in labels_value

            email = Email(
                id=mail_id,
                subject=subject,
                from_raw=from_raw,
                date=date_formatted,
                is_unread=is_unread,
            )
            mails.append(email)
        return mails

    def create_label(self, name):
        body = {"name": name}
        response = (
            self.service.users().labels().create(userId="me", body=body).execute()
        )
        return response

    def apply_label(self, mail_id, label_id):
        body = {"addLabelIds": [label_id]}
        response = (
            self.service.users()
            .messages()
            .modify(userId="me", id=mail_id, body=body)
            .execute()
        )
        return response

    def create_filter(self, sender_email, label_id):
        body = {
            "criteria": {"from": sender_email},
            "action": {"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]},
        }
        response = (
            self.service.users()
            .settings()
            .filters()
            .create(userId="me", body=body)
            .execute()
        )

        return response
