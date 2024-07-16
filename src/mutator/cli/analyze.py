import hashlib
import pathlib

import click

from ..helper.metrics import dstrloc, locfrac, strloc
from ..helper.timed import timed


@click.command(help="Analyze the dataset generated with `collect`.")
@click.option(
    "--dataset",
    type=pathlib.Path,
    default=pathlib.Path("out", "dataset", "data"),
    help="Path to dataset.",
    show_default=True,
)
@click.option(
    "--metric",
    type=click.Choice(
        ["dloc", "source_loc", "mutation_loc", "loc_frac", "prompt_loc"],
        case_sensitive=False,
    ),
    help="""
    Metric used to inspect dataset. If not specified the full dataset will be dumped.
    """,
)
@timed
def dataset(dataset, metric):
    import datasets
    import matplotlib.pyplot as plt
    import pandas

    dataset = datasets.load_from_disk(str(dataset), keep_in_memory=True)
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


@click.command(
    help="Inspects trainig samples based on the loss value received during training.",
)
@click.option(
    "--dir",
    type=pathlib.Path,
    help="Path to training/model output directory.",
)
@click.option(
    "-d",
    "--dataset",
    type=pathlib.Path,
    help="Path to dataset used during training.",
)
@click.option(
    "--min-loss",
    type=float,
    default=2.0,
    help="Ignore all training samples with a loss less than this value.",
)
@timed
def train_result(dir, dataset, min_loss):
    import datasets
    import matplotlib.pyplot as plt
    import pandas

    def _hash(b: bytes) -> str:
        hasher = hashlib.new("sha256")
        hasher.update(b)
        return hasher.hexdigest()

    dataset = datasets.load_from_disk(str(dataset), keep_in_memory=True)
    dataset = dataset.map(lambda r: {**r, "hash": _hash(r["prompt"].encode())})
    print(dataset)

    fig, ax = plt.subplots(nrows=2)

    train_file = "file://" + str((dir / "train-series.json").absolute())
    train_series = pandas.read_json(train_file, orient="split", typ="series")
    print(train_series.describe([0.25, 0.5, 0.75, 0.9, 0.95, 0.995]))

    def _dataset_to_dataframe(d: datasets.Dataset) -> dict:
        hash = []
        prompt = []
        for row in d:
            hash.append(_hash(row["prompt"].encode()))
            prompt.append(row["prompt"])
        return {"index": hash, "data": {"prompt": prompt}, "columns": ["prompt"]}

    train_ds_series = pandas.DataFrame(**_dataset_to_dataframe(dataset))
    train_info = train_ds_series.merge(train_series, left_index=True, right_index=True)
    print(train_info)
    train_info = train_info.loc[train_info["train-loss"] > min_loss]
    train_info = train_info.sort_values(by=["train-loss"])
    print(train_info)

    from ..inspect.analyze import Analyze

    app = Analyze(train_info)
    app.run()
