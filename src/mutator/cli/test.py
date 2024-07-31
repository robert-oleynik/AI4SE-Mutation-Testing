import multiprocessing
import os
import pathlib
import shutil
import subprocess
import tempfile

import click

from ..helper.pattern import Filter
from ..helper.timed import timed
from ..result import Result
from ..store import MutantStore


def _run_tester(x):
    pid = os.getpid()
    (
        tmp_dir,
        project_dir,
        timeout,
        git_reset,
        module_name,
        target_name,
        i,
        mutant,
        source,
    ) = x

    project = f"{tmp_dir}/{pid}"
    if not os.path.exists(project):

        def ignore_outdir(dir, contents):
            return ["out"]

        shutil.copytree(project_dir, project, ignore=ignore_outdir)

    if git_reset:
        subprocess.run(["git", "reset", "--hard"], capture_output=True, cwd=project)

    args = [
        "python3",
        "-m",
        "mutator_runner",
        "-m",
        module_name,
        "-p",
        os.path.abspath(mutant),
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

    is_syntax_error = exit_code is not None and exit_code > 1 and not is_timeout
    is_dead = exit_code != 0
    output = output if output != "" else output_err
    return (
        module_name,
        target_name,
        mutant,
        source,
        is_dead,
        is_syntax_error,
        is_timeout,
        output,
    )


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
@click.option(
    "-j",
    "--jobs",
    type=int,
    default=4,
    help="Number of parallel jobs to execut in parallel",
)
@timed
def test(out_dir, project, filter, timeout, git_reset, test_dropped, jobs):
    tempdir = tempfile.mkdtemp(prefix="mutator-test")

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

    targets = [
        (
            tempdir,
            project,
            timeout,
            git_reset,
            module_name,
            target_name,
            i,
            mutant,
            source,
        )
        for module_name, module in mutants.items()
        for target_name, target in sorted(list(module.items()), key=lambda v: v[0])
        for i, (mutant, source) in enumerate(target)
        if filters.should_include(f"{module_name}:{target_name}")
    ]
    timeout_count = 0
    syntax_error_count = 0
    dead = 0
    count = len(targets)

    def status_update(name: str, index: int):
        live = index - dead - syntax_error_count - timeout_count  # noqa: B023
        print(
            f"{name:<80} [{index}/{count}]",  # noqa: B023
            f"dead: {dead} live: {live}",  # noqa: B023
            f"syntax errors: {syntax_error_count} timeout: {timeout_count}",  # noqa: B023
            end="\r",
        )

    with multiprocessing.Pool(processes=jobs) as p:
        i = 0
        for x in p.imap(_run_tester, targets):
            (
                module_name,
                target_name,
                mutant,
                source,
                is_dead,
                is_syntax_error,
                is_timeout,
                output,
            ) = x
            status_update(f"{module_name}:{target_name}", i)
            result.insert(
                module_name,
                target_name,
                mutant.stem,
                mutant.absolute().relative_to(out_dir.resolve("./mutants")),
                source,
                is_dead,
                is_syntax_error,
                is_timeout,
                output,
            )
            if is_dead and not is_syntax_error and not is_timeout:
                dead += 1
            if is_syntax_error:
                syntax_error_count += 1
            if is_timeout:
                timeout_count += 1
            i += 1
    print()
    result.write(out_dir / "test-result.json")
    shutil.rmtree(tempdir)
