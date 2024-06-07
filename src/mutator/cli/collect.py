import pathlib
import shutil
import typing

import click
from git import Repo

from ..collect import TestMods

strategies = {"test_mods": TestMods()}


def generate_samples(
    bare_repos: list[pathlib.Path],
    git: list[pathlib.Path],
    strategy: list[str],
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
                    yield sample

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
@click.option("-s", "--strategy", multiple=True, default=list(strategies.keys()))
def collect(out_dir, bare, git, strategy):
    import datasets

    cache_dir = out_dir / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    data = datasets.Dataset.from_generator(
        generate_samples(bare, git, strategy), keep_in_memory=True, cache_dir=cache_dir
    )
    data.save_to_disk((out_dir / "data").__str__())
