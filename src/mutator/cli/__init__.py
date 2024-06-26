import click

from .analyze import dataset, train_result
from .collect import collect
from .generate import generate
from .inspect import inspect
from .test import test
from .train import train


@click.group(chain=True)
def cli():
    pass


cli.add_command(generate)
cli.add_command(test)
cli.add_command(inspect)
cli.add_command(collect)
cli.add_command(train)
cli.add_command(dataset)
cli.add_command(train_result)

__all__ = [
    "cli",
]
