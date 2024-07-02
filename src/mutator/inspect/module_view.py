import difflib
import json
import pathlib

from textual.app import ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.scroll_view import ScrollableContainer
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
    def __init__(self, out_dir: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        self._name = None
        self._mutations = None
        self._selected = 0
        self.out_dir = out_dir
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
                f"[{int(id) + 1}/{len(self._mutations)}]  {self._name}"
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
            file = (self.out_dir / mutation["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            for annotation in metadata.get("annotations", []):
                label += ", " + annotation
            self.lbl_mutation.update(label)

    def select_next(self) -> None:
        self._selected = (self._selected + 1) % len(self._mutations)
        self._update()

    def select_prev(self) -> None:
        self._selected = (self._selected - 1) % len(self._mutations)
        self._update()

    def compose(self) -> ComposeResult:
        yield self.lbl_module
        yield self.lbl_mutation


class TargetDiff(TextArea):
    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path, **kwargs):
        super().__init__("", read_only=True, **kwargs)
        self.base_dir = base_dir
        self.out_dir = out_dir

    def update(self, target):
        try:
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
            self.load_text("".join(lines))
        except FileNotFoundError as e:
            self.load_text(str(e))


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
            del metadata["mutation"]
            self._meta = metadata
            self._pretty.update(metadata)
        except FileNotFoundError as e:
            self._pretty.update(e)

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(self._pretty)


class TargetView(Widget):
    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        self._header = TargetHeader(out_dir, classes="target-header")
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
        self._annotation_editor.value = json.dumps(
            self._info._meta.get("annotations", ["_"])
        )
        self._mutation = mutation

    def on_button_pressed(self, ev: Button.Pressed) -> None:
        if ev.button.name == "next":
            self._header.select_next()
        elif ev.button.name == "prev":
            self._header.select_prev()
        else:
            return
        self.update(self._header._name, self._header._mutations)

    def on_input_changed(self, ev: Input.Changed) -> None:
        if ev.input.name == "annotation" and self._mutation is not None:
            try:
                file = (self._out_dir / self._mutation["file"]).with_suffix(".json")
                metadata = json.load(open(file))
                metadata["annotations"] = json.loads(ev.input.value)
                json.dump(metadata, open(file, "w"))
                del metadata["mutation"]
                self._info._pretty.update(metadata)

                ev.input.remove_class("invalid")
                ev.input.add_class("valid")
            except json.JSONDecodeError:
                ev.input.remove_class("valid")
                ev.input.add_class("invalid")

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
