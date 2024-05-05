import pathlib
import logging

import pytest

from .dependency_injector import DependencyInjector
from .mutation import Mutation, MutationStore
from .project import Project


def run_tests(workingDir: pathlib.Path | None = None,
              buildDir: pathlib.Path | None = None) -> None:
    if workingDir is None:
        workingDir = pathlib.Path.cwd()
    if buildDir is None:
        buildDir = pathlib.Path.cwd().joinpath("build/mutations")

    p = Project(workingDir)
    p.log_info()

    mutations = []
    for source in p.sources:
        for target in source.targets:
            # TODO : Generate mutation
            mutation = target.content(source.content)
            mutations.append(Mutation(source, target, mutation))
    mutationStore = MutationStore(buildDir, mutations)

    if len(mutations) == 0:
        logging.error("no mutations found")
        exit(1)

    # TODO: Pass pytest flags
    injector = DependencyInjector(mutationStore)
    injector.install()
    while injector.next_mutation():
        if pytest.main(["-s", workingDir.__str__()]) == 0:
            print("test suite passed for mutation:")
            print("======")
            print(injector.current_diff())
            print("======")
    injector.uninstall()
