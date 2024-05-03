from .project import Project
import pathlib
import pytest

def run_tests(workingDir: pathlib.Path | None = None) -> None:
    workingDir = pathlib.Path.cwd() if workingDir is None else workingDir
    p = Project(workingDir)
    p.log_info()

    p.scan_files()
    pytest.main()
