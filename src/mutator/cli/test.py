import argparse
import pathlib
import subprocess
import time

from ..store import MutationStore
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
            **other):
        if chdir is None:
            chdir = pathlib.Path.cwd()
        if out_dir is None:
            out_dir = chdir.joinpath("out/mutations")
        if not skip_generation:
            self.generate.run(out_dir, generator, chdir)

        mutation = {}
        store = MutationStore(out_dir)
        for module, target, path in store.list_mutation():
            if module not in mutation:
                mutation[module] = {}
            if target not in mutation[module]:
                mutation[module][target] = []
            mutation[module][target].append(path)

        spinner = Spinner()
        for module_name, module in mutation.items():
            print("Testing Module:", module_name)
            for target_name, target in module.items():
                catched = 0
                for i, mutation in enumerate(target):
                    print(f" {spinner} {target_name} [{i}/{len(target)}]", end="\r")
                    args = [
                            "python3", "-m", "mutator.runner",
                            "-m", module_name,
                            "-p", mutation
                    ]
                    process = subprocess.Popen(
                            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    while process.poll() is None:
                        time.sleep(.1)
                        spinner.next()
                        print(f" {spinner} {target_name:<32} [{i}/{len(target)}]", end="\r")
                    if process.poll() != 0:
                        catched += 1
                print(f" ✔ {target_name:<32} [{len(target)}/{len(target)}] catched:", catched, "missed:", len(target) - catched)
