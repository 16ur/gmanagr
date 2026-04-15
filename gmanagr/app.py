from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, DataTable, ListView, ListItem, Label
from textual.screen import ModalScreen
from gmanagr.auth import checkToken
from gmanagr.gmail_client import GmailClient


class Gmanagr(App):
    THEME = "catppuccin-mocha"
    BINDINGS = [
        ("d", "toggle_dark", "change theme"),
        ("x", "label_email", "label email"),
    ]

    async def on_mount(self) -> None:
        self.theme = "catppuccin-mocha"
        table = self.query_one(DataTable)
        table.add_column("Date", width=20)
        table.add_column("From", width=25)
        table.add_column("Subject", width=40)

        creds = checkToken()
        self.client = GmailClient(creds)
        self.mails = self.client.get_messages(1)

        for mail in self.mails:
            table.add_row(
                mail.date, self.client.get_from_email(mail.from_raw), mail.subject
            )

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()

    def action_label_email(self):
        table = self.query_one(DataTable)
        row_index = table.cursor_row
        self.selected_email = self.mails[row_index]
        labels = self.client.get_labels()
        self.push_screen(LabelSelectScreen(labels), callback=self._on_label_selected)

    def refresh_emails(self):
        table = self.query_one(DataTable)
        table.clear()
        self.mails = self.client.get_messages(1)
        for mail in self.mails:
            table.add_row(mail.date, mail.from_raw, mail.subject)

    def _on_label_selected(self, result):
        if result is None:
            return
        self.client.apply_label(self.selected_email.id, result["id"])
        from_email = self.client.get_from_email(self.selected_email.from_raw)
        self.client.create_filter(from_email, result["id"])
        self.refresh_emails()


class LabelSelectScreen(ModalScreen):
    def __init__(self, labels):
        super().__init__()
        self.labels = labels

    def compose(self):
        yield ListView(
            *[
                ListItem(Label(label["name"]), id=f"label-{label['id']}")
                for label in self.labels
            ]
        )

    def on_list_view_selected(self, event: ListView.Selected):
        item_id = event.item.id
        label_id = item_id.replace("label-", "", 1)
        label = next(label for label in self.labels if label["id"] == label_id)
        self.dismiss(label)
