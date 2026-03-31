from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, DataTable
from gmanagr.auth import checkToken
from gmanagr.gmail_client import GmailClient, Email


class Gmanagr(App):
    THEME = "catppuccin-mocha"
    BINDINGS = [("d", "toggle_dark", "change theme")]
    
    async def on_mount(self) -> None:
        self.theme = "catppuccin-mocha"
        table = self.query_one(DataTable)
        table.add_columns("Date", "From", "Subject")
        
        creds = checkToken()
        client = GmailClient(creds)
        mails = client.get_messages(1)
        
        for mail in mails:
            table.add_row(mail.date, mail.from_raw, mail.subject)
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable()
