import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmanagr.models import Email


class GmailClient:
    def __init__(self, creds):
        self.creds = creds
        self._local = threading.local()

    def _service(self):
        if not hasattr(self._local, "service"):
            self._local.service = build("gmail", "v1", credentials=self.creds)
        return self._local.service

    def get_labels(self):
        labels = self._service().users().labels().list(userId="me").execute()
        return [item for item in labels.get("labels", []) if item["type"] == "user"]

    def get_messages(self, days: int) -> list[Email]:
        after = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
        result = self._service().users().messages().list(userId="me", q=f"after:{after} in:inbox").execute()
        msg_ids = [msg["id"] for msg in result.get("messages", [])]

        def fetch(msg_id: str) -> Email:
            response = (
                self._service().users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
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
            return Email(
                id=response["id"],
                subject=subject,
                from_raw=from_raw,
                date=local_time,
                is_unread="UNREAD" in response["labelIds"],
            )

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch, msg_id): msg_id for msg_id in msg_ids}
            emails = {}
            for future in as_completed(futures):
                emails[futures[future]] = future.result()

        return [emails[msg_id] for msg_id in msg_ids if msg_id in emails]

    def create_label(self, name: str):
        return self._service().users().labels().create(userId="me", body={"name": name}).execute()

    def trash_message(self, mail_id: str):
        return self._service().users().messages().trash(userId="me", id=mail_id).execute()

    def apply_label(self, mail_id: str, label_id: str):
        return (
            self._service().users()
            .messages()
            .modify(userId="me", id=mail_id, body={"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]})
            .execute()
        )

    def batch_apply_label(self, mail_ids: list[str], label_id: str):
        return (
            self._service().users()
            .messages()
            .batchModify(userId="me", body={"ids": mail_ids, "addLabelIds": [label_id], "removeLabelIds": ["INBOX"]})
            .execute()
        )

    def create_filter(self, sender_email: str, label_id: str):
        body = {
            "criteria": {"from": sender_email},
            "action": {"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]},
        }
        try:
            return (
                self._service().users().settings().filters().create(userId="me", body=body).execute()
            )
        except HttpError as e:
            if e.status_code == 400:
                return None
            raise

    def get_from_email(self, from_raw: str) -> str:
        match = re.search(r"<(.+?)>", from_raw)
        return match.group(1) if match else from_raw
