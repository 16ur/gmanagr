from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Label, ListItem, ListView, Static
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
        ("backspace", "Trash"),
        ("t", "Time range"),
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
        ("t", "change_days", "Time range"),
        ("backspace", "trash_email", "Trash"),
    ]

    days = reactive(2)

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
        panel.loading = True
        self._update_panel_title()

        self._init_and_load()

    def _update_panel_title(self) -> None:
        days = self.days
        label = "day" if days == 1 else "days"
        self.query_one("#mail-panel").border_title = f"Inbox — last {days} {label}"

    @work(thread=True)
    def _init_and_load(self) -> None:
        creds = checkToken()
        self.client = GmailClient(creds)
        mails = self.client.get_messages(self.days)
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
        if result["id"] is None:
            result = self.client.create_label(result["name"])
        self.client.apply_label(self.selected_email.id, result["id"])
        from_email = self.client.get_from_email(self.selected_email.from_raw)
        self.client.create_filter(from_email, result["id"])
        mails = self.client.get_messages(self.days)
        self.call_from_thread(self._populate_table, mails)

    def action_trash_email(self) -> None:
        if not hasattr(self, "client") or not hasattr(self, "mails"):
            return
        table = self.query_one(DataTable)
        self.selected_email = self.mails[table.cursor_row]
        subject = self.selected_email.subject
        self.push_screen(
            ConfirmScreen(f'Move to trash?\n"{subject}"'),
            callback=self._on_trash_confirmed,
        )

    def _on_trash_confirmed(self, confirmed: bool | None) -> None:
        if not confirmed:
            return
        self.query_one("#mail-panel").loading = True
        self._trash_and_reload()

    @work(thread=True)
    def _trash_and_reload(self) -> None:
        self.client.trash_message(self.selected_email.id)
        mails = self.client.get_messages(self.days)
        self.call_from_thread(self._populate_table, mails)

    def action_change_days(self) -> None:
        self.push_screen(DaysInputScreen(self.days), callback=self._on_days_changed)

    def _on_days_changed(self, days: int | None) -> None:
        if days is None:
            return
        self.days = days
        self.query_one("#mail-panel").loading = True
        self._update_panel_title()
        self._reload_emails()

    @work(thread=True)
    def _reload_emails(self) -> None:
        mails = self.client.get_messages(self.days)
        self.call_from_thread(self._populate_table, mails)


class ConfirmScreen(ModalScreen):
    BINDINGS = [
        ("enter", "confirm", "Confirm"),
        ("escape", "dismiss", "Cancel"),
    ]

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        panel = Static(self.message, id="confirm-message")
        panel.border_title = "Confirm"
        yield Vertical(
            panel,
            Static("↵ confirm  esc cancel", classes="modal-footer"),
            id="confirm-wrapper",
        )

    def action_confirm(self) -> None:
        self.dismiss(True)


class DaysInputScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Cancel")]

    def __init__(self, current_days: int):
        super().__init__()
        self.current_days = current_days

    def compose(self) -> ComposeResult:
        inp = Input(
            value=str(self.current_days),
            placeholder="Number of days...",
            id="days-input",
        )
        inp.border_title = "Time range"
        yield Vertical(
            inp,
            Static("↵ confirm  esc cancel", classes="modal-footer"),
            id="days-wrapper",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        try:
            days = int(event.value.strip())
            if days > 0:
                self.dismiss(days)
        except ValueError:
            pass


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
            lv,
            Input(placeholder="New label...", id="new-label-input"),
            Static("tab create  esc cancel", classes="modal-footer"),
            id="modal-wrapper",
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        label_id = item_id.replace("label-", "", 1)
        label = next(label for label in self.labels if label["id"] == label_id)
        self.dismiss(label)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if name:
            self.dismiss({"id": None, "name": name})
