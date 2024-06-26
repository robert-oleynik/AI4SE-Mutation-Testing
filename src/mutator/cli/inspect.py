import pathlib

import click

from ..inspect.app import InspectApp


@click.command()
@click.option(
    "-o",
    "--out-dir",
    type=pathlib.Path,
    default=pathlib.Path("out", "mutations"),
    show_default=True,
)
@click.option(
    "-p",
    "--project",
    type=pathlib.Path,
    default=pathlib.Path("."),
    show_default=True,
    help="Change project directory",
)
def inspect(out_dir, project):
    app = InspectApp(project, out_dir)
    app.run()
