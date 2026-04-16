from dataclasses import dataclass


@dataclass
class Email:
    id: str
    subject: str
    from_raw: str
    date: str
    is_unread: bool
