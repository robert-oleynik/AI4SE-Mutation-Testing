import pathlib

from textual.app import App, ComposeResult
from textual.widgets import ListView

from ..result import Result
from .module_view import Target, TargetList, TargetView


class InspectApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    .module-list {
        border: solid white;
        width: 1fr;
    }
    .module-view {
        layout: vertical;
        width: 4fr;
    }
    .target-header {
        layout: horizontal;
        height: 3;
        border: solid white;
    }
    .header-first {
        width: 1fr;
    }
    .header-last {
        width: 1fr;
        text-align: right;
    }
    .target-diff {
        border: solid white;
        height: 2fr;
    }
    .target-log {
        border: solid white;
        height: 1fr;
        width: 2fr;
    }
    .target-info {
        width: 1fr;
        height: 1fr;
        border: solid white;
    }
    .target-view-toolbar {
        height: 3;
    }
    .toolbar-button {
        width: 1fr;
    }
    .toolbar-spacer {
        width: 1;
    }
    .valid {
        border: green;
    }
    .invalid {
        border: red;
    }
    """

    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path):
        super().__init__()
        self.result = Result(path=out_dir / "test-result.json")
        self.target_list = TargetList(self.result, classes="module-list")
        self.target_view = TargetView(base_dir, out_dir, classes="module-view")

    def on_list_view_highlighted(self, ev: ListView.Highlighted) -> None:
        target = ev.item
        if isinstance(target, Target):
            self.target_view.update(target._name, target._target)

    def on_mount(self) -> None:
        module = self.target_list.modules[0]
        self.target_view.update(module._name, module._target)

    def compose(self) -> ComposeResult:
        yield self.target_list
        yield self.target_view
