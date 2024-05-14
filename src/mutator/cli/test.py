import argparse
import pathlib
import subprocess
import time

from ..store import MutationStore
from ..source import Filter
from ..result import Result
from .generate import Generate
from .spinner import Spinner


class Test:
    """
    Configues and runs CLI command to run pytest for all mutations.
    Will nest the generate command.
    """

    def __init__(self):
        self.generate = Generate()

    def add_arguments(self, parser: argparse.ArgumentParser):
        self.generate.add_arguments(parser)
        parser.add_argument(
                "-s", "--skip-generation",
                action="store_true",
                default=False,
                help="Reuse already generated mutations.")

    def run(self,
            out_dir: pathlib.Path,
            generator: list[str],
            chdir: pathlib.Path,
            skip_generation: bool,
            filters: list[str],
            **other):
        if chdir is None:
            chdir = pathlib.Path.cwd()
        if out_dir is None:
            out_dir = chdir.joinpath("out/mutations")
        if not skip_generation:
            ec = self.generate.run(out_dir, generator, chdir, filters=filters, **other)
            if ec != 0:
                return ec

        f = Filter(filters)

        mutation = {}
        store = MutationStore(out_dir)
        for module, target, path, source in store.list_mutation():
            if module not in mutation:
                mutation[module] = {}
            if target not in mutation[module]:
                mutation[module][target] = []
            mutation[module][target].append((path, source))

        result = Result()

        spinner = Spinner()
        for module_name, module in mutation.items():
            print("Testing Module:", module_name)
            for target_name, target in sorted(list(module.items()), key=lambda v: v[0]):
                if not f.match(module_name, target_name):
                    continue
                catched = 0
                count = len(target)
                for i, (mutation, source) in enumerate(target):
                    print(f" {spinner} {target_name:<32} [{i}/{count}]", end="\r")
                    args = [
                            "python3", "-m", "mutator_runner",
                            "-m", module_name,
                            "-p", mutation
                    ]
                    process = subprocess.Popen(
                            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd = chdir)
                    while process.poll() is None:
                        time.sleep(.1)
                        spinner.next()
                        print(f" {spinner} {target_name:<32} [{i}/{count}]", end="\r")
                    is_catched = process.poll() != 0
                    result.insert(module_name,
                                  target_name,
                                  mutation.stem,
                                  mutation.absolute().relative_to(out_dir.resolve("./mutations")),
                                  source,
                                  is_catched)
                    if is_catched:
                        catched += 1
                print(f" ✔ {target_name:<32} [{count}/{count}] catched:",
                      catched, "missed:", len(target) - catched)
        result.write(out_dir / "test-result.json")
