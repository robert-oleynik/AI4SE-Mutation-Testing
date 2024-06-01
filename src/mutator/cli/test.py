import pathlib
import subprocess
import time

import click

from ..result import Result
from ..source import Filter
from ..store import MutationStore
from .spinner import Spinner


@click.command()
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "mutations"),
    type=pathlib.Path,
    show_default=True,
    help="Directory used to store mutations",
)
@click.option(
    "-p",
    "--project",
    default=pathlib.Path("."),
    type=pathlib.Path,
    show_default=True,
    help="Project to run tests on",
)
@click.option(
    "-f",
    "--filter",
    multiple=True,
    help="Specify select filter for identifying mutations",
)
@click.option(
    "-t", "--timeout", type=int, default=60, help="Test suite timeout in seconds"
)
def test(out_dir, project, filter, timeout):
    filters = Filter(filter)

    mutation = {}
    store = MutationStore(out_dir)
    for module, target, path, source in store.list_mutation():
        if module not in mutation:
            mutation[module] = {}
        if target not in mutation[module]:
            mutation[module][target] = []
        mutation[module][target].append((path, source))

    result = Result()

    timeout *= 10
    spinner = Spinner()
    for module_name, module in mutation.items():
        print("Testing Module:", module_name)
        for target_name, target in sorted(list(module.items()), key=lambda v: v[0]):
            if not filters.match(module_name, target_name):
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
                    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project
                )
                counter = 0
                while process.poll() is None and counter < timeout:
                    time.sleep(0.1)
                    spinner.next()
                    print(f" {spinner} {target_name:<80} [{i}/{count}]", end="\r")
                    counter += 1
                if counter >= timeout:
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
                    counter >= timeout,
                    output,
                )
                if is_caught and counter < timeout:
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
