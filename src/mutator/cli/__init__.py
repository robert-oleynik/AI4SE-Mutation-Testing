import click

from .collect import collect
from .generate import generate
from .inspect import inspect
from .test import test


@click.group(chain=True)
def cli():
    pass


cli.add_command(generate)
cli.add_command(test)
cli.add_command(inspect)
cli.add_command(collect)

__all__ = [
    "cli",
]
