import logging
import os
from pathlib import Path

def run(workingDir: Path = None):
	workingDir = Path.cwd() if workingDir == None else workingDir
	project = Project(workingDir)
	project.log_info()
