import argparse
import difflib
import pathlib

import textual.app
import textual.containers
import textual.scroll_view
import textual.widgets

from ..result import Result


class Inspector(textual.app.App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    .box {
        height: 100%;
        border: solid white;
    }
    .side-modules {
        width: 3fr;
    }
    .side-mutations {
        width: 2fr;
    }
    .side-diff {
        width: 10fr;
    }
    .diff-code {
        width: 100%;
        height: 3fr;
        border: solid white;
    }
    .diff-log {
        width: 100%;
        height: 2fr;
        border: solid white;
    }
    """

    def init(self, chdir: pathlib.Path, out_dir: pathlib.Path):
        self.chdir = chdir
        self.out_dir = out_dir
        self.selected_node = None
        self.focus = 0

        self.result = Result(path=out_dir / "mutations" / "test-result.json")
        self.modules_tree = textual.widgets.Tree("Modules")
        self.modules_tree.show_root = False
        for name, module in self.result.modules.items():
            targets = [
                (name, any([not r["caught"] for m, r in target.items()]))
                for name, target in module.items()
            ]
            color = "green"
            if any(map(lambda x: x[1], targets)):
                color = "red"
            node = self.modules_tree.root.add(f"[{color}]{name}[/{color}]", expand=True)
            targets.sort(key=lambda x: 1 - int(x[1]))
            for name, failed in targets:
                color = "green"
                if failed:
                    color = "red"
                node.add(
                    f"[{color}]{name}[/{color}]", data=module[name], allow_expand=False
                )
        self.mutations = textual.widgets.ListView()
        self.code = textual.widgets.TextArea.code_editor(
            "", language="python", theme="dracula", read_only=True, classes="diff-code"
        )
        self.textLog = textual.widgets.TextArea.code_editor(
            "", read_only=True, classes="diff-log"
        )

    def update_diff(self):
        if self.selected_node is None:
            return
        index = self.selected_mutations
        keys = [k for k in self.selected_node.data.keys()]
        key = keys[index]
        file = self.out_dir / "mutations" / self.selected_node.data[key]["file"]
        file_lines = list(
            map(lambda line: line.decode(), file.read_bytes().splitlines(True))
        )
        source = self.chdir / "src" / self.selected_node.data[key]["source"]
        source_lines = list(
            map(lambda line: line.decode(), source.read_bytes().splitlines(True))
        )

        lines = difflib.unified_diff(
            source_lines, file_lines, fromfile=f"{file}", tofile=f"{source}"
        )
        diff = [line for line in lines]
        self.code.load_text("".join(diff))
        self.textLog.load_text(self.selected_node.data[key]["output"])

    def on_tree_node_highlighted(self, msg: textual.widgets.Tree.NodeSelected):
        if msg.node.data is None:
            return
        self.selected_node = msg.node
        self.selected_mutations = 0
        self.mutations.clear()
        for name, info in msg.node.data.items():
            label = textual.widgets.Static(f"[green]{name}[/green]")
            if not info["caught"]:
                label = textual.widgets.Static(f"[red]{name}[/red]")
            self.result = label.children
            self.mutations.append(textual.widgets.ListItem(label))
        self.selected_mutations = 0
        self.update_diff()

    def on_list_view_highlighted(self, msg: textual.widgets.ListView.Highlighted):
        if msg.item is None:
            return
        self.selected_mutations = self.mutations.children.index(msg.item)
        self.update_diff()

    def on_key(self, ev: textual.events.Key):
        if ev.key == "right":
            self.focus = (self.focus + 1) % 3
            pass
        elif ev.key == "left":
            self.focus = (3 + self.focus - 1) % 3
        if self.focus == 0:
            self.modules_tree.focus()
        elif self.focus == 1:
            self.mutations.focus()
        else:
            self.code.focus()

    def compose(self) -> textual.app.ComposeResult:
        yield textual.scroll_view.ScrollView(
            self.modules_tree, classes="box side-modules"
        )
        yield textual.scroll_view.ScrollView(
            self.mutations, classes="box side-mutations"
        )
        yield textual.containers.Vertical(self.code, self.textLog, classes="side-diff")


class Inspect:
    """
    Provide information about the generated mutations for the current project.
    """

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "-o",
            "--out-dir",
            action="store",
            type=pathlib.Path,
            help="Output directory.",
        )
        parser.add_argument(
            "-c",
            "--chdir",
            action="store",
            type=pathlib.Path,
            default=pathlib.Path.cwd(),
            help="Change working directory",
        )

    def run(self, out_dir: pathlib.Path | None, chdir: pathlib.Path, **other):
        if out_dir is None:
            out_dir = chdir / "out"
        app = Inspector()
        app.init(chdir, out_dir)
        app.run()
