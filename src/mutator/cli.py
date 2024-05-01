import argparse
import logging
from pathlib import Path

from .test import run_tests


def main():
    parser = argparse.ArgumentParser(prog="mutation-tester",
        description="Run tests with mutated source code.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    subcommands = parser.add_subparsers(required=True,dest="command")
    test_parser = subcommands.add_parser("test")
    test_parser.add_argument("-c", "--chdir",
        action="store",
        type=Path,
        help="Set working directory. Defaults to current directory.")
    subcommands.add_parser("help")
    args = parser.parse_args()

    level=logging.DEBUG
    if args.verbose == 0 or args.verbose is None:
        level=logging.WARN
    elif args.verbose == 1:
        level=logging.INFO
    logging.basicConfig(format="%(message)s", encoding="utf-8", level=level)

    match args.command:
        case "test":
            logging.debug("executing test command")
            run_tests(workingDir=args.chdir)
        case "help":
            parser.print_help()

if __name__=="__main__":
    main()
