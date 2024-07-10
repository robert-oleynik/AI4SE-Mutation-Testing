import difflib
import json
import pathlib

from textual.app import ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.scroll_view import ScrollableContainer
from textual.suggester import SuggestFromList
from textual.widget import Widget
from textual.widgets import Button, Input, ListItem, ListView, Pretty, Static, TextArea

from ..result import Result


class Target(ListItem):
    def __init__(self, name: str, mutations: list[(str, dict)], **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._mutations = mutations

    def render(self) -> RenderResult:
        if self.is_everything_caught():
            return f"[green]{self._name}[/green]"
        return f"[red]{self._name}[/red]"

    def is_everything_caught(self) -> bool:
        return all(m["caught"] for _, m in self._mutations)


class TargetList(Widget):
    def __init__(self, result: Result, **kwargs):
        super().__init__(**kwargs)

        def mutations_sort_key(item):
            _, mutation = item
            return mutation["caught"]

        targets = [
            Target(
                f"{modname}:{name}",
                list(sorted(mutations.items(), key=mutations_sort_key)),
            )
            for modname, module in result.modules.items()
            for name, mutations in module.items()
        ]
        self.modules = sorted(targets, key=lambda m: m.is_everything_caught())

    def compose(self) -> ComposeResult:
        yield ListView(*self.modules)


class TargetHeader(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = None
        self._mutations = None
        self._selected = 0
        self.lbl_module = Static(classes="header-first")
        self.lbl_mutation = Static(classes="header-last")

    def on_mount(self) -> None:
        self._update()

    def update(self, name: str, mutations) -> None:
        if self._name != name:
            self._name = name
            self._mutations = mutations
            self._selected = 0
        self._update()

    def _update(self) -> None:
        if self._mutations is not None and self._selected < len(self._mutations):
            id, mutation = self._mutations[self._selected]
            self.lbl_module.update(
                f"[{self._selected + 1}/{len(self._mutations)}] (id {id}) {self._name}"
            )
            label = ""
            if mutation["caught"]:
                label += "[green]"
                if mutation.get("syntax_error", False):
                    label += "syntax error"
                elif mutation.get("timeout", False):
                    label += "timeout"
                else:
                    label += "caught"
                label += "[/green]"
                self.remove_class("invalid")
                self.add_class("valid")
            else:
                label += "[red]missed[/red]"
                self.remove_class("valid")
                self.add_class("invalid")
            self.lbl_mutation.update(label)

    def cycle_selected(self, offset: int) -> None:
        self._selected = (self._selected + offset) % len(self._mutations)
        self._update()

    def compose(self) -> ComposeResult:
        yield self.lbl_module
        yield self.lbl_mutation


class TargetDiff(TextArea):
    LLM_RESULT_KEYS = [None, "prompt", "output", "transformed", "final"]

    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path, **kwargs):
        super().__init__("", read_only=True, **kwargs)
        self.base_dir = base_dir
        self.out_dir = out_dir
        self.llm_result_stage = 0

    def llm_result_key(self):
        return self.LLM_RESULT_KEYS[self.llm_result_stage]

    def cycle_llm_result_stage(self, offset: int):
        self.llm_result_stage = (self.llm_result_stage + offset) % len(
            self.LLM_RESULT_KEYS
        )

    def update(self, target):
        try:
            text = (
                self.get_diff(target)
                if self.llm_result_key() is None
                else self.get_llm_result_stage(target)
            )
            self.load_text(text)
        except FileNotFoundError as e:
            self.load_text(str(e))

    def get_diff(self, target):
        file = self.out_dir / target["file"]
        file_lines = list(
            map(lambda line: line.decode(), file.read_bytes().splitlines(True))
        )
        source = self.base_dir / "src" / target["source"]
        source_lines = list(
            map(lambda line: line.decode(), source.read_bytes().splitlines(True))
        )

        lines = difflib.unified_diff(
            source_lines, file_lines, fromfile=f"{file}", tofile=f"{source}"
        )
        return "".join(lines)

    def get_llm_result_stage(self, target):
        file = (self.out_dir / target["file"]).with_suffix(".json")
        metadata = json.load(open(file))
        try:
            return metadata["llm"][self.llm_result_key()]
        except KeyError:
            return (
                f"The llm result stage {self.llm_result_key()} "
                + "is not defined for this mutation"
            )


class TargetLog(TextArea):
    def __init__(self, **kwargs):
        super().__init__("", read_only=True, **kwargs)

    def update(self, target):
        self.load_text(target["output"])


class TargetInfo(Widget):
    def __init__(self, out_dir: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = out_dir
        self._pretty = Pretty(None)
        self._meta = {}

    def update(self, target):
        try:
            file = (self.out_dir / target["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            for key in ["mutation", "llm"]:
                if key in metadata:
                    del metadata[key]
            self._meta = metadata
            self._pretty.update(metadata)
        except FileNotFoundError as e:
            self._pretty.update(e)

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(self._pretty)


class TargetView(Widget):
    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        self._header = TargetHeader(classes="target-header")
        self._content = TargetDiff(base_dir, out_dir, classes="target-diff")
        self._log = TargetLog(classes="target-log")
        self._info = TargetInfo(out_dir, classes="target-info")
        self._annotation_editor = Input(
            value="", name="annotation", classes="annotation-input valid"
        )
        self._mutation = None
        self._out_dir = out_dir

    def update(self, name: str, mutations) -> None:
        self._header.update(name, mutations)
        _, mutation = mutations[self._header._selected]
        self._content.update(mutation)
        self._log.update(mutation)
        self._info.update(mutation)
        self._annotation_editor.value = ", ".join(
            self._info._meta.get("annotations", [])
        )
        self._mutation = mutation

    def update_with_current(self):
        self.update(self._header._name, self._header._mutations)

    def action_cycle_mutation(self, offset: int):
        self._header.cycle_selected(offset)
        self.update_with_current()

    def action_cycle_llm_result_stage(self, offset: int):
        self._content.cycle_llm_result_stage(offset)
        self.update_with_current()

    def action_annotate(self):
        if self._mutation is None:
            return

        def annotate(annotation: str) -> None:
            annotation = annotation.strip()
            if annotation == "":
                return
            file = (self._out_dir / self._mutation["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            metadata["annotations"] = metadata.get("annotations", []) + [annotation]
            self._annotation_editor.value = ", ".join(metadata["annotations"])
            json.dump(metadata, open(file, "w"))
            del metadata["mutation"]
            self._info._pretty.update(metadata)

        self.app.push_screen(AnnotateScreen(), annotate)

    def on_button_pressed(self, ev: Button.Pressed) -> None:
        if ev.button.name == "next":
            self.action_select_next_mutation()
        elif ev.button.name == "prev":
            self.action_select_prev_mutation()

    def on_input_changed(self, ev: Input.Changed) -> None:
        if ev.input.name == "annotation" and self._mutation is not None:
            annotations = [
                annotation.strip() for annotation in ev.input.value.split(",")
            ]
            file = (self._out_dir / self._mutation["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            metadata["annotations"] = annotations
            json.dump(metadata, open(file, "w"))
            del metadata["mutation"]
            self._info._pretty.update(metadata)

    def compose(self) -> ComposeResult:
        yield self._header
        yield self._content
        yield Horizontal(self._log, self._info)
        yield Horizontal(
            Button("Prev", name="prev", classes="toolbar-button"),
            Static(" ", classes="toolbar-spacer"),
            self._annotation_editor,
            Static(" ", classes="toolbar-spacer"),
            Button("Next", name="next", classes="toolbar-button"),
            classes="target-view-toolbar",
        )


class AnnotateScreen(ModalScreen[str]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app.update_all_annotations()
        self.input = Input(
            value="",
            suggester=SuggestFromList(self.app.all_annotations),
        )

    def compose(self):
        yield self.input

    def on_input_submitted(self):
        self.dismiss(self.input.value)
