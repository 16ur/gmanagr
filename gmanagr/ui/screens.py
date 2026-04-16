from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView, Static


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
            Static("↵ create  esc cancel", classes="modal-footer"),
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
