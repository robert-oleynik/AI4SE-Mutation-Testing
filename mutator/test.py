import os
from pathlib import Path
import logging

def run(workingDir: Path = None):
	workingDir = Path.cwd() if workingDir == None else workingDir
	logging.info("working directory: %s", workingDir)
