import pathlib

import click

from ..helper.metrics import dstrloc, locfrac, strloc
from ..inspect.app import InspectApp


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
    if int(tui) + int(dataset is not None) > 1:
        print("error: only one option out of `--dataset` and `--tui` is allowed")
        exit(1)
    if tui:
        app = InspectApp(project, out_dir)
        app.run()
    if dataset is not None:
        import datasets
        import matplotlib.pyplot as plt
        import pandas

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
