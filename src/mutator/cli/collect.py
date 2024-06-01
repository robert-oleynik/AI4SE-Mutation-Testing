import json
import pathlib

import click
from git import Repo

from ..collect import TestMods

strategies = {"test_mods": TestMods()}


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
    def _run(path: pathlib.Path, repo: Repo):
        print("repository", path.stem)
        f = out_dir / f"{path.stem}.json"
        report = {"git": {"origin": repo.remote("origin").url}, "samples": {}}
        for s in strategy:
            report["samples"][s] = []
            if s not in strategies:
                raise Exception("no such strategy '" + s + "'")
            print(f"- applying strategy '{s}' ", end="")
            c = 0
            for sample in strategies[s].apply(repo):
                c += 1
                print(f"\r{f"- applying strategy '{s}'":<60}[samples: {c}] ", end="")
                report["samples"][s].append(sample.build())
            print()
        json.dump(report, f.open("w+"))

    out_dir.mkdir(parents=True, exist_ok=True)
    for path in git:
        repo = Repo.init(path)
        _run(path, repo)
    for path in bare:
        repo = Repo.init(path, bare=True)
        _run(path, repo)
