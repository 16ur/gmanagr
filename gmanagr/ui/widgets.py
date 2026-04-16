from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

from gmanagr.models import Email


def _row_cells(mail: Email, from_email: str):
    if mail.is_unread:
        return (
            Text(mail.date, style="bold"),
            Text(from_email, style="bold"),
            Text(mail.subject, style="bold"),
        )
    return (mail.date, from_email, mail.subject)


class AppHeader(Horizontal):
    unread_count = reactive(0)

    def compose(self) -> ComposeResult:
        yield Static("gmanagr", id="header-title")
        yield Static("·", id="header-sep")
        yield Static("Gmail manager", id="header-subtitle")
        yield Static("", id="header-unread")

    def watch_unread_count(self, count: int) -> None:
        label = self.query_one("#header-unread", Static)
        label.update(f"● {count} unread" if count > 0 else "")


class AppFooter(Horizontal):
    BINDINGS_INFO = [
        ("x", "Label email"),
        ("⌫", "Trash"),
        ("t", "Time range"),
        ("d", "Toggle theme"),
    ]

    def compose(self) -> ComposeResult:
        for key, desc in self.BINDINGS_INFO:
            yield Static(key, classes="key-badge")
            yield Static(desc, classes="key-desc")
