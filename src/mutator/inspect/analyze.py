import pandas
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static, TextArea


class Analyze(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    Button {
        height: 3;
        width: 1fr;
    }
    .header {
        border: solid white;
        height: 3;
    }
    .content {
        border: solid white;
        height: 1fr;
    }
    """

    def __init__(self, data: pandas.DataFrame):
        super().__init__()
        self._selected = 0
        self._data = data
        self._header = Static(classes="header")
        self._content = TextArea("", classes="content")

    def _update(self):
        _s = self._selected
        _d = len(self._data)
        self._header.update(
            f"[{_s + 1}/{_d}] {self._data.index[_s]} (loss: {self._data.values[_s][1]})"
        )
        self._content.load_text(self._data.values[_s][0])

    def on_mount(self):
        self._update()

    def on_button_pressed(self, ev: Button.Pressed) -> None:
        if ev.button.name == "prev":
            self._selected = (self._selected - 1 + len(self._data)) % len(self._data)
        elif ev.button.name == "next":
            self._selected = (self._selected + 1) % len(self._data)
        self._update()

    def compose(self) -> ComposeResult:
        yield self._header
        yield self._content
        yield Horizontal(
            Button("Prev", name="prev"),
            Button("Next", name="next"),
        )
