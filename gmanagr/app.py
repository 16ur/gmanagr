from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, ListItem, ListView, Static
from gmanagr.auth import checkToken
from gmanagr.gmail_client import GmailClient


def _row_cells(mail, from_email):
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
        ("d", "Toggle theme"),
    ]

    def compose(self) -> ComposeResult:
        for key, desc in self.BINDINGS_INFO:
            yield Static(key, classes="key-badge")
            yield Static(desc, classes="key-desc")


class Gmanagr(App):
    THEME = "catppuccin-mocha"
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle theme"),
        ("x", "label_email", "Label email"),
    ]

    def compose(self) -> ComposeResult:
        yield AppHeader()
        yield Container(DataTable(), id="mail-panel")
        yield AppFooter()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_column("Date", width=22)
        table.add_column("From", width=30)
        table.add_column("Subject", width=55)

        panel = self.query_one("#mail-panel")
        panel.border_title = "Inbox"
        panel.loading = True

        self._init_and_load()

    @work(thread=True)
    def _init_and_load(self) -> None:
        creds = checkToken()
        self.client = GmailClient(creds)
        mails = self.client.get_messages(1)
        self.call_from_thread(self._populate_table, mails)

    def _populate_table(self, mails) -> None:
        self.mails = mails
        table = self.query_one(DataTable)
        table.clear()
        for mail in mails:
            table.add_row(*_row_cells(mail, self.client.get_from_email(mail.from_raw)))
        unread = sum(1 for m in self.mails if m.is_unread)
        self.query_one(AppHeader).unread_count = unread
        self.query_one("#mail-panel").loading = False

    def action_label_email(self) -> None:
        if not hasattr(self, "client") or not hasattr(self, "mails"):
            return
        table = self.query_one(DataTable)
        self.selected_email = self.mails[table.cursor_row]
        self._fetch_labels()

    @work(thread=True)
    def _fetch_labels(self) -> None:
        labels = self.client.get_labels()
        self.call_from_thread(self.push_screen, LabelSelectScreen(labels), self._on_label_selected)

    def _on_label_selected(self, result) -> None:
        if result is None:
            return
        self.query_one("#mail-panel").loading = True
        self._apply_and_refresh(result)

    @work(thread=True)
    def _apply_and_refresh(self, result) -> None:
        self.client.apply_label(self.selected_email.id, result["id"])
        from_email = self.client.get_from_email(self.selected_email.from_raw)
        self.client.create_filter(from_email, result["id"])
        mails = self.client.get_messages(1)
        self.call_from_thread(self._populate_table, mails)


class LabelSelectScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Cancel")]

    def __init__(self, labels):
        super().__init__()
        self.labels = labels

    def compose(self) -> ComposeResult:
        lv = ListView(
            *[
                ListItem(Label(label["name"]), id=f"label-{label['id']}")
                for label in self.labels
            ]
        )
        lv.border_title = "Select a label"
        yield Vertical(
            lv, Static("esc  cancel", classes="modal-footer"), id="modal-wrapper"
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        label_id = item_id.replace("label-", "", 1)
        label = next(label for label in self.labels if label["id"] == label_id)
        self.dismiss(label)
