from pathlib import Path

from .project import Project


def run_tests(workingDir: Path | None = None) -> None:
    workingDir = Path.cwd() if workingDir is None else workingDir
    project = Project(workingDir)
    project.log_info()
