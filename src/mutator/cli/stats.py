import json
import pathlib

import click

from ..result import Result
from ..store import MutationStore


@click.command()
@click.option(
    "-o",
    "--out-dir",
    type=pathlib.Path,
    default=pathlib.Path("out", "mutations"),
    show_default=True,
)
def stats(out_dir):
    store = MutationStore(out_dir)
    total = {}
    per_generator = {}
    categories = set(["mutations", "caught", "syntax_error", "timeout", "missed"])

    def insert_stat(group: dict, category: str):
        group[category] = group.get(category, 0) + 1

    def stat(category: str, generator: str):
        categories.add(category)
        insert_stat(total, category)
        insert_stat(per_generator.setdefault(generator, {}), category)

    test_result = Result.read(out_dir / "test-result.json")
    for module, target, path, _ in store.list_mutation():
        metadata = json.load(open(path.with_suffix(".json")))
        generator = metadata["generator"]
        stat("mutations", generator)
        for annotation in metadata.get("annotations", []):
            stat(annotation, generator)
        if test_result:
            result = test_result[module][target][path.stem]
            syntax_error = result.get("syntax_error", False)
            timeout = result.get("timeout", False)
            caught = result.get("caught", False)
            missed = not caught
            caught = caught and not timeout and not syntax_error
            for category, is_category in [
                ("caught", caught),
                ("syntax_error", syntax_error),
                ("timeout", timeout),
                ("missed", missed),
            ]:
                if is_category:
                    stat(category, generator)

    categories = list(sorted(categories))
    for name, group in [("total", total), *sorted(per_generator.items())]:
        name = f" {name} "
        print(f"{name:=^40}")
        for category in categories:
            count = group.get(category, 0)
            category = category + ":"
            print(f"{category:<20}{count:>20}")
