from textual.app import App, ComposeResult
from textual.widgets import Footer, Header


class Gmanagr(App):
    THEME = "catppuccin-mocha"
    BINDINGS = [("d", "toggle_dark", "change theme")]
    
    def on_mount(self) -> None:
        self.theme = "catppuccin-mocha"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
