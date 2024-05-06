import argparse
import pathlib

from ..store import MutationStore


class Inspect:
    """
    Provide information about the generated mutations for the current project.
    """

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
                "-o", "--out-dir",
                action="store",
                type=pathlib.Path,
                help="Output directory.")

    def run(self, out_dir: pathlib.Path, **other):
        if out_dir is None:
            out_dir = pathlib.Path.cwd().joinpath("out/mutations")
        store = MutationStore(out_dir)
        for module, target, path in store.list_mutation():
            print(module, target, path)
