import json
import pathlib

from git import Repo

import collector.strategy


def run(
    git: pathlib.Path, out: pathlib.Path, strategies: list[str], bare: bool, **other
) -> int:
    for name in other.keys():
        print(f"error: unkown argument '{name}'")
        return 1

    print("loading git repository")
    repo = Repo.init(git, bare=bare)

    print("collecting samples:")
    report = {"git": {"origin": repo.remote("origin").url}, "samples": {}}
    for s in strategies:
        report["samples"][s] = []
        if s not in collector.strategy.strategies:
            raise Exception("no such strategy '" + s + "'")
        print(f"- applying strategy '{s}'", end=" ")
        counter = 0
        for sample in collector.strategy.strategies[s].apply(repo):
            counter += 1
            print(f"\r{f"- applying strategy '{s}'":<60}[samples: {counter}] ", end="")
            report["samples"][s].append(sample.build())
        print()
    json.dump(report, out.open("w+"))
    return 0
