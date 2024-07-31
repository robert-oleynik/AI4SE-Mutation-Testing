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
    def __init__(self, name: str, mutants: list[(str, dict)], **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._mutants = mutants

    def render(self) -> RenderResult:
        if self.is_everything_dead():
            return f"[green]{self._name}[/green]"
        return f"[red]{self._name}[/red]"

    def is_everything_dead(self) -> bool:
        return all(m.get("dead") or m["caught"] for _, m in self._mutants)


class TargetList(Widget):
    def __init__(self, result: Result, **kwargs):
        super().__init__(**kwargs)

        def mutants_sort_key(item):
            _, mutant = item
            return mutant.get("dead") or mutant["caught"]

        targets = [
            Target(
                f"{modname}:{name}",
                list(sorted(mutants.items(), key=mutants_sort_key)),
            )
            for modname, module in result.modules.items()
            for name, mutants in module.items()
        ]
        self.modules = sorted(targets, key=lambda m: m.is_everything_dead())

    def compose(self) -> ComposeResult:
        yield ListView(*self.modules)


class TargetHeader(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = None
        self._mutants = None
        self._selected = 0
        self.lbl_module = Static(classes="header-first")
        self.lbl_mutant = Static(classes="header-last")

    def on_mount(self) -> None:
        self._update()

    def update(self, name: str, mutants) -> None:
        if self._name != name:
            self._name = name
            self._mutants = mutants
            self._selected = 0
        self._update()

    def _update(self) -> None:
        if self._mutants is not None and self._selected < len(self._mutants):
            id, mutant = self._mutants[self._selected]
            self.lbl_module.update(
                f"[{self._selected + 1}/{len(self._mutants)}] (id {id}) {self._name}"
            )
            label = ""
            if mutant.get("dead") or mutant["caught"]:
                label += "[green]"
                if mutant.get("syntax_error", False):
                    label += "syntax error"
                elif mutant.get("timeout", False):
                    label += "timeout"
                else:
                    label += "dead"
                label += "[/green]"
                self.remove_class("invalid")
                self.add_class("valid")
            else:
                label += "[red]live[/red]"
                self.remove_class("valid")
                self.add_class("invalid")
            self.lbl_mutant.update(label)

    def cycle_selected(self, offset: int) -> None:
        self._selected = (self._selected + offset) % len(self._mutants)
        self._update()

    def compose(self) -> ComposeResult:
        yield self.lbl_module
        yield self.lbl_mutant


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
                + "is not defined for this mutant"
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
            for key in ["mutant", "mutation", "llm"]:
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
        self._mutant = None
        self._out_dir = out_dir

    def update(self, name: str, mutants) -> None:
        self._header.update(name, mutants)
        _, mutant = mutants[self._header._selected]
        self._content.update(mutant)
        self._log.update(mutant)
        self._info.update(mutant)
        self._annotation_editor.value = ", ".join(
            self._info._meta.get("annotations", [])
        )
        self._mutant = mutant

    def update_with_current(self):
        self.update(self._header._name, self._header._mutants)

    def action_cycle_mutant(self, offset: int):
        self._header.cycle_selected(offset)
        self.update_with_current()

    def action_cycle_llm_result_stage(self, offset: int):
        self._content.cycle_llm_result_stage(offset)
        self.update_with_current()

    def action_annotate(self):
        if self._mutant is None:
            return

        def annotate(annotation: str) -> None:
            annotation = annotation.strip()
            if annotation == "":
                return
            file = (self._out_dir / self._mutant["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            self.app.add_annotations([annotation])
            metadata["annotations"] = metadata.get("annotations", []) + [annotation]
            self._annotation_editor.value = ", ".join(metadata["annotations"])
            json.dump(metadata, open(file, "w"))
            self._info.update(self._mutant)

        self.app.push_screen(AnnotateScreen(), annotate)

    def on_button_pressed(self, ev: Button.Pressed) -> None:
        if ev.button.name == "next":
            self.action_cycle_mutant(1)
        elif ev.button.name == "prev":
            self.action_cycle_mutant(-1)

    def on_input_changed(self, ev: Input.Changed) -> None:
        if ev.input.name == "annotation" and self._mutant is not None:
            annotations = [
                annotation.strip() for annotation in ev.input.value.split(",")
            ]
            annotations = [annotation for annotation in annotations if annotation != ""]
            file = (self._out_dir / self._mutant["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            self.app.remove_annotations(metadata.get("annotations", []))
            self.app.add_annotations(annotations)
            metadata["annotations"] = annotations
            json.dump(metadata, open(file, "w"))
            self._info.update(self._mutant)

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
        self.input = Input(
            value="",
            suggester=SuggestFromList(list(self.app.all_annotations.keys())),
        )

    def compose(self):
        yield self.input

    def on_input_submitted(self):
        self.dismiss(self.input.value)
