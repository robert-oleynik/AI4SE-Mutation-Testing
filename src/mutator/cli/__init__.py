import click

from .generate import generate
from .inspect import inspect
from .test import test


@click.group(chain=True)
def cli():
    pass


cli.add_command(generate)
cli.add_command(test)
cli.add_command(inspect)

__all__ = [
    "cli",
    "generate",
    "Test",
]
