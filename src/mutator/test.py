from pathlib import Path

from project import Project


def run(workingDir: Path = None):
    workingDir = Path.cwd() if workingDir is None else workingDir
    project = Project(workingDir)
    project.log_info()
