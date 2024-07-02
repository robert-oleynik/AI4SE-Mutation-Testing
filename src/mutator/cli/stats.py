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
@click.option(
    "--show-dropped",
    is_flag=True,
    default=False,
    show_default=True,
    help="Include stats of dropped mutations",
)
def stats(out_dir, show_dropped):
    store = MutationStore(out_dir)
    total = {}
    per_generator = {}
    categories = set(
        ["mutations", "dropped", "caught", "syntax_error", "timeout", "missed"]
    )

    def insert_stat(group: dict, category: str, value: int):
        group[category] = group.get(category, 0) + value

    def stat(category: str, generator: str, value=1):
        categories.add(category)
        insert_stat(total, category, value)
        insert_stat(per_generator.setdefault(generator, {}), category, value)

    test_result = Result.read(out_dir / "test-result.json")
    for module, target, path, _, metadata in store.list_mutation():
        generator = metadata["generator"]
        if metadata.get("dropped", False):
            stat("dropped", generator)
            if not show_dropped:
                continue
        else:
            stat("mutations", generator)
        for annotation in metadata.get("annotations", []):
            stat(annotation, generator)
        for llm_stat, value in metadata.get("llm_stats", {}).items():
            stat(f"llm_{llm_stat}", generator, value)
        if test_result:
            try:
                result = test_result[module][target][path.stem]
            except AttributeError:
                continue
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
            print(f"{category:<30}{count:>10}")
