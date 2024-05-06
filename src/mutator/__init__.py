import argparse

import mutator.cli


def cli_main() -> int:
    parser = argparse.ArgumentParser(
            prog="mutator",
            description="Pytest runner for mutated source code.")
    subcommands = parser.add_subparsers(required=True,dest="command")
    for name, handle in mutator.cli.commands.items():
        p = subcommands.add_parser(name)
        handle.add_arguments(p)

    args = parser.parse_args()
    for name, handle in mutator.cli.commands.items():
        if args.command == name:
            return handle.run(**args.__dict__)
    return 1
