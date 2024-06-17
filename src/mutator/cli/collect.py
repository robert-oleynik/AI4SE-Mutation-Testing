import pathlib
import shutil
import typing

import click
from git import Repo

from ..collect import TestMods
from ..generator import CommentRewriteGenerator, RepeatGenerator
from ..helper.metrics import dstrloc, locfrac, strloc

formatter = {
    "repeat": RepeatGenerator(),
    "rewrite": CommentRewriteGenerator(),
}

strategies = {"test_mods": TestMods()}


def generate_samples(
    bare_repos: list[pathlib.Path],
    git: list[pathlib.Path],
    strategy: list[str],
    formatter_names: list[str],
) -> typing.Generator[dict, None, None]:
    def _gen():
        repos = list(map(lambda g: (True, g), bare_repos)) + list(
            map(lambda g: (False, g), git)
        )
        for bare, path in repos:
            repo = Repo.init(path, bare=bare)
            counter = 0
            for s in strategy:
                if s not in strategies:
                    continue
                for sample in strategies[s].apply(repo):
                    counter += 1
                    for name in formatter_names:
                        s = sample.to_dict(formatter[name])
                        s["formatter"] = name
                        yield s

    return _gen


@click.command(help="Extract mutation samples from repository")
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "dataset"),
    type=pathlib.Path,
    show_default=True,
    help="Directory used to store extracted samples",
)
@click.option(
    "-b",
    "--bare",
    multiple=True,
    type=pathlib.Path,
    help="Bare git repositories to extract mutations from",
)
@click.option(
    "-g",
    "--git",
    multiple=True,
    type=pathlib.Path,
    help="Git repositories to extract mutations from",
)
@click.option(
    "--max-dloc",
    default=20,
    type=int,
    help="Drop all entries with more change in loc than this value",
)
@click.option(
    "--max-loc-ratio",
    default=10.0,
    type=float,
    help="Max ration between mutation LOC and source LOC",
)
@click.option(
    "--update",
    is_flag=True,
    help="Update Dataset in place without regenerating (Will ignore git repositories)",
)
@click.option("--max-prompt-loc", default=1024, type=int, help="Max LOC for prompt")
@click.option("-s", "--strategy", multiple=True, default=list(strategies.keys()))
def collect(
    out_dir, bare, git, strategy, max_dloc, max_loc_ratio, max_prompt_loc, update
):
    import datasets

    def _loc_ratio(row):
        f = locfrac(row["source"], row["mutation"])
        return 1 / max_loc_ratio <= f and f <= max_loc_ratio

    cache_dir = out_dir / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    if update:
        data = datasets.load_from_disk(dataset_path=(out_dir / "data").__str__())
    else:
        data = datasets.Dataset.from_generator(
            generate_samples(bare, git, strategy, ["rewrite"]),
            keep_in_memory=True,
            cache_dir=cache_dir,
        )
    data = data.filter(
        lambda row: abs(dstrloc(row["source"], row["mutation"])) < max_dloc
    )
    data = data.filter(_loc_ratio)
    data = data.filter(lambda row: strloc(row["prompt"]) < max_prompt_loc)
    if update:
        data.save_to_disk((out_dir / "data-updated").__str__())
    else:
        data.save_to_disk((out_dir / "data").__str__())
