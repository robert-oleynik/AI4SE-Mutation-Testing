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
@click.option(
    "--git-reset",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run git reset --hard before each run of the test suite",
)
def test(out_dir, project, filter, timeout, git_reset):
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
            syntax_error_count = 0
            caught = 0
            count = len(target)

            def status_update(icon: str, index: int, **kwargs):
                missed = index - caught - syntax_error_count - timeout_count  # noqa: B023
                print(
                    f" {icon} {target_name:<80} [{index}/{count}]",  # noqa: B023
                    f"caught: {caught} missed: {missed}",  # noqa: B023
                    f"syntax errors: {syntax_error_count} timeout: {timeout_count}",  # noqa: B023
                    **kwargs,
                )

            for i, (mutation, source) in enumerate(target):
                status_update(spinner, i, end="\r")
                if git_reset:
                    subprocess.run(
                        ["git", "reset", "--hard"], capture_output=True, cwd=project
                    )
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
                    status_update(spinner, i, end="\r")
                    counter += 1
                process.kill()
                exit_code = process.poll()
                is_timeout = counter >= timeout
                is_syntax_error = (
                    exit_code is not None and exit_code > 1 and not is_timeout
                )
                is_caught = exit_code != 0
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
                    is_syntax_error,
                    is_timeout,
                    output,
                )
                if is_caught and not is_syntax_error and not is_timeout:
                    caught += 1
                if is_syntax_error:
                    syntax_error_count += 1
                if is_timeout:
                    timeout_count += 1
            status_update("✔", count)
    result.write(out_dir / "test-result.json")
