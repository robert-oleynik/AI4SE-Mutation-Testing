import argparse
import pathlib
import subprocess
import time

from ..result import Result
from ..source import Filter
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
            "-s",
            "--skip-generation",
            action="store_true",
            default=False,
            help="Reuse already generated mutations.",
        )
        parser.add_argument(
            "--test-timeout",
            action="store",
            default=60,
            type=int,
            help="Test suite timeout in seconds",
        )

    def run(
        self,
        out_dir: pathlib.Path,
        generators: list[str],
        chdir: pathlib.Path,
        skip_generation: bool,
        filters: list[str],
        test_timeout: int,
        **other,
    ):
        if chdir is None:
            chdir = pathlib.Path.cwd()
        if out_dir is None:
            out_dir = chdir.joinpath("out/mutations")
        if not skip_generation:
            ec = self.generate.run(
                out_dir=out_dir,
                generators=generators,
                chdir=chdir,
                filters=filters,
                **other,
            )
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

        test_timeout *= 10
        spinner = Spinner()
        for module_name, module in mutation.items():
            print("Testing Module:", module_name)
            for target_name, target in sorted(list(module.items()), key=lambda v: v[0]):
                if not f.match(module_name, target_name):
                    continue
                timeout_count = 0
                caught = 0
                count = len(target)
                for i, (mutation, source) in enumerate(target):
                    print(f" {spinner} {target_name:<80} [{i}/{count}]", end="\r")
                    args = [
                        "python3",
                        "-m",
                        "mutator_runner",
                        "-m",
                        module_name,
                        "-p",
                        mutation,
                    ]
                    process = subprocess.Popen(
                        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=chdir
                    )
                    counter = 0
                    while process.poll() is None and counter < test_timeout:
                        time.sleep(0.1)
                        spinner.next()
                        print(f" {spinner} {target_name:<80} [{i}/{count}]", end="\r")
                        counter += 1
                    if counter >= test_timeout:
                        timeout_count += 1
                    process.kill()
                    is_caught = process.poll() != 0
                    output = process.stdout.read().decode()
                    output_err = process.stderr.read().decode()
                    output = output if output != "" else output_err
                    result.insert(
                        module_name,
                        target_name,
                        mutation.stem,
                        mutation.absolute().relative_to(out_dir.resolve("./mutations")),
                        source,
                        is_caught,
                        counter >= test_timeout,
                        output,
                    )
                    if is_caught and counter < test_timeout:
                        caught += 1
                print(
                    f" ✔ {target_name:<80} [{count}/{count}] caught:",
                    caught,
                    "missed:",
                    len(target) - caught - timeout_count,
                    "timeout:",
                    timeout_count,
                )
        result.write(out_dir / "test-result.json")
