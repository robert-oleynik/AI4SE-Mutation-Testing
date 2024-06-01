import argparse
import pathlib

from .cli import run
from .strategy import strategies


def cli_main() -> int:
    parser = argparse.ArgumentParser(
        prog="mutator", description="Dataset collector for mutation testing"
    )
    parser.add_argument(
        "-g",
        "--git",
        action="store",
        type=pathlib.Path,
        help="Path to (bare) git repository",
    )
    parser.add_argument(
        "-o",
        "--out",
        action="store",
        type=pathlib.Path,
        help="Path to store dataset at.",
    )
    parser.add_argument(
        "-b",
        "--bare",
        action="store_true",
        help="specified repo is a bare repository",
    )
    parser.add_argument("strategies", nargs="*", type=str, default=strategies.keys())
    args = parser.parse_args()
    return run(**args.__dict__)
