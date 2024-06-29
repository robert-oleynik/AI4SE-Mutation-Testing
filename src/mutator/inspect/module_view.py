import difflib
import json
import pathlib

from textual.app import ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, ListItem, ListView, Pretty, Static, TextArea

from ..result import Result


class Target(ListItem):
    def __init__(self, name: str, target, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._target = target

    def render(self) -> RenderResult:
        if self.is_everything_caught():
            return f"[green]{self._name}[/green]"
        return f"[red]{self._name}[/red]"

    def is_everything_caught(self) -> bool:
        if not all(r["caught"] for _, r in self._target.items()):
            return False
        return True


class TargetList(Widget):
    def __init__(self, result: Result, **kwargs):
        super().__init__(**kwargs)
        targets = [
            Target(f"{modname}:{name}", target)
            for modname, module in result.modules.items()
            for name, target in module.items()
        ]
        self.modules = sorted(targets, key=lambda m: int(m.is_everything_caught()))

    def compose(self) -> ComposeResult:
        yield ListView(*self.modules)


class TargetHeader(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = None
        self._target = None
        self._selected = 0
        self.lbl_module = Static(classes="header-first")
        self.lbl_target = Static(classes="header-last")

    def on_mount(self) -> None:
        self._update()

    def update(self, name: str, target) -> None:
        if self._name != name:
            self._name = name
            self._target = target
            self._selected = 0
        self._update()

    def _update(self) -> None:
        if self._name is not None and self._target is not None:
            self.lbl_module.update(
                f"[{self._selected + 1}/{len(self._target)}]  {self._name}"
            )
        if self._target is not None and self._selected < len(self._target):
            mutation = self._target[str(self._selected)]
            if mutation["caught"]:
                self.lbl_target.update("[green]caught[/green]")
                if self.has_class("invalid"):
                    self.remove_class("invalid")
                if not self.has_class("valid"):
                    self.add_class("valid")
            else:
                if "timeout" in mutation and mutation["timeout"]:
                    self.lbl_target.update("[red]timeout[/red]")
                else:
                    self.lbl_target.update("[red]caught[/red]")
                if self.has_class("valid"):
                    self.remove_class("valid")
                if not self.has_class("invalid"):
                    self.add_class("invalid")

    def select_next(self) -> None:
        self._selected = (self._selected + 1) % len(self._target)
        self._update()

    def select_prev(self) -> None:
        self._selected = (self._selected - 1 + len(self._target)) % len(self._target)
        self._update()

    def compose(self) -> ComposeResult:
        yield self.lbl_module
        yield self.lbl_target


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


class TargetInfo(Pretty):
    def __init__(self, out_dir: pathlib.Path, **kwargs):
        super().__init__(None, **kwargs)
        self.out_dir = out_dir

    def update(self, target):
        try:
            file = (self.out_dir / target["file"]).with_suffix(".json")
            metadata = json.load(open(file))
            del metadata["mutation"]
            super().update(metadata)
        except FileNotFoundError as e:
            super().update(e)


class TargetView(Widget):
    def __init__(self, base_dir: pathlib.Path, out_dir: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        self._header = TargetHeader(classes="target-header")
        self._content = TargetDiff(base_dir, out_dir, classes="target-diff")
        self._log = TargetLog(classes="target-log")
        self._info = TargetInfo(out_dir, classes="target-info")

    def update(self, name: str, target) -> None:
        self._header.update(name, target)
        mutation = target[str(self._header._selected)]
        self._content.update(mutation)
        self._log.update(mutation)
        self._info.update(mutation)

    def on_button_pressed(self, ev: Button.Pressed) -> None:
        if ev.button.name == "next":
            self.target_view._header.select_next()
        elif ev.button.name == "prev":
            self.target_view._header.select_prev()
        else:
            return
        self.target_view.update(
            self.target_view._header._name, self.target_view._header._target
        )

    def compose(self) -> ComposeResult:
        yield self._header
        yield self._content
        yield Horizontal(self._log, self._info)
        yield Horizontal(
            Button("Prev", name="prev", classes="toolbar-button"),
            Static(" ", classes="toolbar-spacer"),
            Button("Next", name="next", classes="toolbar-button"),
            classes="target-view-toolbar",
        )
