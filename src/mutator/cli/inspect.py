import difflib
import json
import pathlib

import click
import textual.app
import textual.containers
import textual.scroll_view
import textual.widgets

from ..helper.metrics import dstrloc, locfrac, strloc
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
        width: 5fr;
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

        self.result = Result(path=out_dir / "test-result.json")
        self.modules_tree = textual.widgets.Tree("Modules")
        self.modules_tree.show_root = False
        for name, module in self.result.modules.items():
            targets = [
                (name, any([not r["caught"] for m, r in target.items()]))
                for name, target in module.items()
            ]
            color = "green"
            if any(map(lambda target: target[1], targets)):
                color = "red"
            node = self.modules_tree.root.add(f"[{color}]{name}[/{color}]", expand=True)
            targets.sort(key=lambda target: (not target[1], target[0]))
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
        self.metadata = textual.widgets.TextArea.code_editor(
            "", language="json", read_only=True
        )

    def update_diff(self):
        if self.selected_node is None:
            return
        index = self.selected_mutations
        keys = [k for k in self.selected_node.data.keys()]
        key = keys[index]
        file = self.out_dir / self.selected_node.data[key]["file"]
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
        metadata = json.load(open(file.with_suffix(".json"), "r"))
        del metadata["mutation"]
        self.metadata.load_text(json.dumps(metadata, indent=4))

    def on_tree_node_highlighted(self, msg: textual.widgets.Tree.NodeSelected):
        if msg.node.data is None:
            return
        self.selected_node = msg.node
        self.selected_mutations = 0
        self.mutations.clear()
        mutations = list(msg.node.data.items())
        mutations.sort(key=lambda mutation: (mutation[1]["caught"], int(mutation[0])))
        for name, info in mutations:
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
        yield textual.containers.Vertical(
            textual.scroll_view.ScrollView(self.mutations),
            self.metadata,
            classes="box side-mutations",
        )
        yield textual.containers.Vertical(self.code, self.textLog, classes="side-diff")


@click.command()
@click.option(
    "-o",
    "--out-dir",
    type=pathlib.Path,
    default=pathlib.Path("out", "mutations"),
    show_default=True,
)
@click.option(
    "-p",
    "--project",
    type=pathlib.Path,
    default=pathlib.Path("."),
    show_default=True,
    help="Change project directory",
)
@click.option("--tui", is_flag=True, help="Open inspector as TUI.")
@click.option(
    "--dataset",
    type=pathlib.Path,
    help="Path to dataset to inspect. Excludes `--tui`.",
    show_default=True,
)
@click.option(
    "--metric",
    type=click.Choice(
        ["dloc", "source_loc", "mutation_loc", "loc_frac", "prompt_loc"],
        case_sensitive=False,
    ),
    help="Metric used to inspect dataset (Ignored if not used with `--dataset`)",
)
def inspect(out_dir, project, tui, dataset, metric):
    import datasets
    import matplotlib.pyplot as plt
    import pandas

    if int(tui) + int(dataset is not None) > 1:
        print("error: only one option out of `--dataset` and `--tui` is allowed")
        exit(1)
    if tui:
        app = Inspector()
        app.init(project, out_dir)
        app.run()
    if dataset is not None:
        dataset = datasets.load_from_disk(dataset.__str__(), keep_in_memory=True)
        print(dataset)

        fig, ax = plt.subplots()
        if metric == "dloc":
            data = [dstrloc(row["source"], row["mutation"]) for row in dataset]
            dloc = pandas.Series(name="dloc", data=data)
            print(dloc.quantile([0.5, 0.75, 0.9, 0.95, 0.995]))
            dloc = dloc.value_counts().sort_index()
            dloc.plot(ax=ax, kind="line")
            ax.set_yscale("log")
        elif metric == "source_loc":
            data = [strloc(entry["source"]) for entry in dataset]
            loc = pandas.Series(name="source loc", data=data)
            print(loc.quantile([0.5, 0.75, 0.9, 0.95, 0.995]))
            loc = loc.value_counts().sort_index()
            loc.plot(ax=ax, kind="line")
            ax.set_yscale("log")
        elif metric == "mutation_loc":
            data = [strloc(entry["mutation"]) for entry in dataset]
            loc = pandas.Series(name="mutation loc", data=data)
            print(loc.quantile([0.5, 0.75, 0.9, 0.95, 0.995]))
            loc = loc.value_counts().sort_index()
            loc.plot(ax=ax, kind="line")
            ax.set_yscale("log")
        elif metric == "loc_frac":
            data = [locfrac(entry["source"], entry["mutation"]) for entry in dataset]
            loc = pandas.Series(name="source loc", data=data)
            print(loc.quantile([0.5, 0.75, 0.9, 0.95, 0.995]))
            loc.plot(ax=ax, kind="hist")
            ax.set_yscale("log")
        elif metric == "prompt_loc":
            data = [strloc(entry["prompt"]) for entry in dataset]
            loc = pandas.Series(name="prompt loc", data=data)
            print(loc.quantile([0.5, 0.75, 0.9, 0.95, 0.995]))
            loc = loc.value_counts().sort_index()
            loc.plot(ax=ax, kind="line")
            ax.set_yscale("log")
        else:
            for row in dataset:
                print(row["prompt"])
                print("=" * 80)
            exit()
        plt.show()
