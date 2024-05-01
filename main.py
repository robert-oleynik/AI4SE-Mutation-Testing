import argparse
import pathlib
import mutator.test
import logging

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="mutation-tester",
		description="Run tests with mutated source code.")
	parser.add_argument("-v", "--verbose", action="count", default=0)
	subcommands = parser.add_subparsers(required=True,dest="command")
	test = subcommands.add_parser("test")
	test.add_argument("-c", "--chdir",
		action="store",
		type=pathlib.Path,
		help="Set working directory. Defaults to current directory.")
	help = subcommands.add_parser("help")
	args = parser.parse_args()

	level=logging.DEBUG
	if args.verbose == 0 or args.verbose == None:
		level=logging.WARN
	elif args.verbose == 1:
		level=logging.INFO
	logging.basicConfig(format="%(message)s", encoding="utf-8", level=level)

	match args.command:
		case "test":
			logging.debug("executing test command")
			mutator.test.run(workingDir=args.chdir)
		case "help":
			parser.print_help()
