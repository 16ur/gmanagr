from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable

from gmanagr.auth import check_token
from gmanagr.gmail_client import GmailClient
from gmanagr.ui.screens import ConfirmScreen, DaysInputScreen, LabelSelectScreen
from gmanagr.ui.widgets import AppFooter, AppHeader, _row_cells


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
        creds = check_token()
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
        from concurrent.futures import ThreadPoolExecutor

        if result["id"] is None:
            result = self.client.create_label(result["name"])
        from_email = self.client.get_from_email(self.selected_email.from_raw)
        same_sender_ids = [
            m.id for m in self.mails
            if self.client.get_from_email(m.from_raw) == from_email
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.client.batch_apply_label, same_sender_ids, result["id"])
            executor.submit(self.client.create_filter, from_email, result["id"])
        mails = self.client.get_messages(self.days)
        self.call_from_thread(self._populate_table, mails)

    def action_trash_email(self) -> None:
        if not hasattr(self, "client") or not hasattr(self, "mails"):
            return
        table = self.query_one(DataTable)
        self.selected_email = self.mails[table.cursor_row]
        self.push_screen(
            ConfirmScreen(f'Move to trash?\n"{self.selected_email.subject}"'),
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
