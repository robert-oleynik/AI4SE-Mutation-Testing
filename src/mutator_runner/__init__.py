import argparse
import pathlib

import pytest

from .injector import DependencyInjector


def cli_main():
    parser = argparse.ArgumentParser(
        prog="mutator", description="Pytest runner for mutated source code."
    )
    parser.add_argument("-m", "--module", action="store")
    parser.add_argument("-p", "--path", action="store")
    parser.add_argument("pytest_args", nargs="*")
    args = parser.parse_args()

    injector = DependencyInjector(args.module, pathlib.Path(args.path))
    injector.install()
    return pytest.main(args.pytest_args)
