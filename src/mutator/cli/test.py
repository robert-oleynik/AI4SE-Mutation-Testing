import pathlib
import subprocess

import click

from ..helper.timed import timed
from ..result import Result
from ..source import Filter
from ..store import MutantStore


@click.command(help="Runs the hole test suite for all mutants.")
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "mutants"),
    type=pathlib.Path,
    show_default=True,
    help="Directory to read mutants from and to store.",
)
@click.option(
    "-p",
    "--project",
    default=pathlib.Path("."),
    type=pathlib.Path,
    show_default=True,
    help="Path to project to run tests on.",
)
@click.option(
    "-f",
    "--filter",
    multiple=True,
    default=["*"],
    help="Specify select filter for identifying mutants.",
)
@click.option(
    "-t", "--timeout", type=int, default=60, help="Test suite timeout in seconds."
)
@click.option(
    "--git-reset",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run git reset --hard before each run of the test suite.",
)
@click.option(
    "--test-dropped",
    is_flag=True,
    default=False,
    show_default=True,
    help="Also run tests on dropped mutants. Used for testing purposes.",
)
@timed
def test(out_dir, project, filter, timeout, git_reset, test_dropped):
    filters = Filter(filter)

    mutants = {}
    store = MutantStore(out_dir)
    for module, target, path, source, metadata in store.list_mutants():
        if not test_dropped and metadata.get("dropped", False):
            continue
        if module not in mutants:
            mutants[module] = {}
        if target not in mutants[module]:
            mutants[module][target] = []
        mutants[module][target].append((path, source))

    result = Result()

    for module_name, module in mutants.items():
        print("Testing Module:", module_name)
        for target_name, target in sorted(list(module.items()), key=lambda v: v[0]):
            if not filters.match(module_name, target_name):
                continue
            timeout_count = 0
            syntax_error_count = 0
            caught = 0
            count = len(target)

            def status_update(index: int, **kwargs):
                missed = index - caught - syntax_error_count - timeout_count  # noqa: B023
                print(
                    f"{target_name:<80} [{index}/{count}]",  # noqa: B023
                    f"caught: {caught} missed: {missed}",  # noqa: B023
                    f"syntax errors: {syntax_error_count} timeout: {timeout_count}",  # noqa: B023
                    **kwargs,
                )

            for i, (mutant, source) in enumerate(target):
                status_update(i, end="\r")
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
                    mutant,
                ]
                try:
                    is_timeout = False
                    process = subprocess.run(
                        args, capture_output=True, cwd=project, timeout=timeout
                    )
                    exit_code = process.returncode
                    output = process.stdout.decode()
                    output_err = process.stderr.decode()
                except subprocess.TimeoutExpired:
                    is_timeout = True
                    exit_code = None
                    output = "<timeout>"
                    output_err = "<timeout>"
                is_syntax_error = (
                    exit_code is not None and exit_code > 1 and not is_timeout
                )
                is_caught = exit_code != 0
                output = output if output != "" else output_err
                result.insert(
                    module_name,
                    target_name,
                    mutant.stem,
                    mutant.absolute().relative_to(out_dir.resolve("./mutants")),
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
            status_update(count)
    result.write(out_dir / "test-result.json")
