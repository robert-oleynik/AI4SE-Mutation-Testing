import logging
from pathlib import Path


class Project:
    """
    Use to manage and extract information about a python project.
    """

    def __init__(self, dir: Path):
        self.projectDir = dir

    def log_info(self):
        logging.info("project directory: %s", self.projectDir)
