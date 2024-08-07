import pathlib
from collections import Counter

from textual.app import App, ComposeResult
from textual.widgets import ListView

from ..result import Result
from ..store import MutantStore
from .module_view import Target, TargetList, TargetView


class InspectApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    .module-list {
        border: solid white;
        width: 1fr;

        ListItem {
            background: $panel;
        }

        ListView > ListItem.--highlight {
            background: blue;
        }
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
    .annotation-input {
        width: 2fr;
        border: solid white;
    }
    .valid {
        border: green;
    }
    .invalid {
        border: red;
    }
    """

    BINDINGS = [
        ("left", "select_prev_mutant()", "Select Previous Mutant"),
        ("right", "select_next_mutant()", "Select Next Mutant"),
        (
            "ctrl+left",
            "select_prev_llm_result_stage()",
            "Select Previous LLM Result Stage",
        ),
        (
            "ctrl+right",
            "select_next_llm_result_stage()",
            "Select Next LLM Result Stage",
        ),
        ("ctrl+a", "annotate()", "Annotate"),
    ]

    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path):
        super().__init__()
        self.out_dir = out_dir
        self.result = Result(path=out_dir / "test-result.json")
        self.target_list = TargetList(self.result, classes="module-list")
        self.target_view = TargetView(base_dir, out_dir, classes="module-view")
        self.all_annotations = Counter()
        self.update_all_annotations()

    def on_list_view_highlighted(self, ev: ListView.Highlighted) -> None:
        target = ev.item
        if isinstance(target, Target):
            self.target_view.update(target._name, target._mutants)

    def update_all_annotations(self):
        self.all_annotations.clear()
        for _, _, _, _, metadata in MutantStore(self.out_dir).list_mutants():
            self.add_annotations(metadata.get("annotations", []))

    def add_annotations(self, annotations: list[str]):
        self.all_annotations.update(annotations)

    def remove_annotations(self, annotations: list[str]):
        self.all_annotations.subtract(annotations)
        # remove non-positive keys
        self.all_annotations += {}

    def action_annotate(self):
        self.target_view.action_annotate()

    def action_select_next_mutant(self):
        self.target_view.action_cycle_mutant(1)

    def action_select_prev_mutant(self):
        self.target_view.action_cycle_mutant(-1)

    def action_select_next_llm_result_stage(self):
        self.target_view.action_cycle_llm_result_stage(1)

    def action_select_prev_llm_result_stage(self):
        self.target_view.action_cycle_llm_result_stage(-1)

    def on_mount(self) -> None:
        target = self.target_list.modules[0]
        self.target_view.update(target._name, target._mutants)

    def compose(self) -> ComposeResult:
        yield self.target_list
        yield self.target_view
