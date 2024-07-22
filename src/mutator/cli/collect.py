import pathlib
import shutil
import typing

import click
from git import Repo

from ..cli.generate import generators
from ..collect import TestMods
from ..generator.generator import NoMutantPossible
from ..helper.metrics import dstrloc, locfrac, strloc
from ..helper.timed import timed

strategies = {"test_mods": TestMods()}


def generate_samples(
    bare_repos: list[pathlib.Path],
    repos: list[pathlib.Path],
    strategy: str,
    generator_names: list[str],
) -> typing.Generator[dict, None, None]:
    def _gen():
        all_repos = list(map(lambda g: (True, g), bare_repos)) + list(
            map(lambda g: (False, g), repos)
        )
        for bare, path in all_repos:
            repo = Repo.init(path, bare=bare)
            counter = 0
            for sample in strategies[strategy].apply(repo):
                counter += 1
                for name in generator_names:
                    try:
                        s = sample.to_dict(generators[name])
                        s["formatter"] = name
                        yield s
                    except NoMutantPossible:
                        pass

    return _gen


@click.command(
    help="""
    Collect mutant samples from git repositories and generate a dataset for training.
    """
)
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "dataset"),
    type=pathlib.Path,
    show_default=True,
    help="Directory used to generate data.",
)
@click.option(
    "-b",
    "--bare",
    multiple=True,
    type=pathlib.Path,
    help="""
    Specify path to a bare git repository used to extract mutant samples from.
    Can be used multiple times.
    """,
)
@click.option(
    "-r",
    "--repository",
    multiple=True,
    type=pathlib.Path,
    help="""
    Specify path to a git repository used to extract mutant samples from.
    Can be used multiple times.
    """,
)
@click.option(
    "--max-dloc",
    default=20,
    type=int,
    help="""
    Remove all samples with a change in lines of code from source to mutant greater
    than this values.
    """,
)
@click.option(
    "--max-loc-ratio",
    default=10.0,
    type=float,
    help="""
    Remove all samples with a ration of lines of code for mutant to source greater
    than this value.
    """,
)
@click.option(
    "--min-prompt-loc",
    default=0,
    type=int,
    help="""
    Removes all samples with a prompt lines of code less than the specified value.
    """,
)
@click.option(
    "--max-prompt-loc",
    default=1024,
    type=int,
    help="""
    Removes all samples with a prompt lines of codes greater than the specified values.
    """,
)
@click.option(
    "--update",
    is_flag=True,
    help="""
    Update Dataset in place without generating new samples (Will ignore specified
    git repositories). The updated dataset will be stored at `<out_dir>/data-updated`
    insted of the default `<out_dir>/data`. Use the first directory for training
    instead.
    """,
)
@click.option(
    "-g",
    "--generator",
    multiple=True,
    type=click.Choice(generators.keys()),
    help="""
    Specify generator to collect and generate samples for. While it is possible to
    use multiple generators, it is not recommended.
    """,
)
@timed
def collect(
    out_dir,
    bare,
    repository,
    max_dloc,
    max_loc_ratio,
    min_prompt_loc,
    max_prompt_loc,
    update,
    generator,
):
    import datasets

    datasets.disable_caching()

    def _loc_ratio(row):
        f = locfrac(row["source"], row["mutant"])
        return 1 / max_loc_ratio <= f and f <= max_loc_ratio

    cache_dir = out_dir / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    if update:
        data = datasets.load_from_disk(dataset_path=(out_dir / "data").__str__())
    else:
        data = datasets.Dataset.from_generator(
            generate_samples(bare, repository, "test_mods", generator),
            features=datasets.Features(
                {
                    "commit": datasets.Value(dtype="string"),
                    "file": datasets.Value(dtype="string"),
                    "start": datasets.Value(dtype="int64"),
                    "end": datasets.Value(dtype="int64"),
                    "source": datasets.Value(dtype="large_string"),
                    "mutant": datasets.Value(dtype="large_string"),
                    "prompt": datasets.Value(dtype="large_string"),
                    "formatter": datasets.Value(dtype="string"),
                }
            ),
        )

    print(data)

    data = data.filter(
        lambda row: abs(dstrloc(row["source"], row["mutant"])) < max_dloc,
        load_from_cache_file=False,
    )
    data = data.filter(
        _loc_ratio,
        load_from_cache_file=False,
    )
    data = data.filter(lambda row: min_prompt_loc < strloc(row["prompt"]))
    data = data.filter(
        lambda row: strloc(row["prompt"]) < max_prompt_loc,
        load_from_cache_file=False,
    )
    if update:
        data.save_to_disk((out_dir / "data-updated").__str__())
    else:
        data.save_to_disk((out_dir / "data").__str__())
