import pathlib

import click

from ..result import Result
from ..store import MutationStore


@click.command(
    help="Display stats produced during testing. Expects `test` to be run before."
)
@click.option(
    "-o",
    "--out-dir",
    type=pathlib.Path,
    default=pathlib.Path("out", "mutations"),
    show_default=True,
    help="Path to mutation directories.",
)
@click.option(
    "--show-dropped",
    is_flag=True,
    default=False,
    show_default=True,
    help="Include stats of dropped mutations.",
)
@click.option(
    "-g",
    "--group-by",
    type=click.Choice(["model_or_checkpoint", "generator", "config_name"]),
    multiple=True,
    default=[],
    help="Attributes by which to group the statistics. "
    + "Specify none to get a total across all mutations.",
)
def stats(out_dir, group_by, show_dropped):
    store = MutationStore(out_dir)
    groups = {}
    count_categories = [
        "mutations",
        "dropped",
        "kept",
        "missed",
        "caught",
        "syntax_error",
        "timeout",
    ]
    llm_categories = set()
    annotation_categories = set()

    test_result = Result.read(out_dir / "test-result.json")
    for module, target, path, _, metadata in store.list_mutation():
        key = []
        for key_name in group_by:
            key.append(metadata.get(key_name, "unknown"))
        key = tuple(key)
        group = groups.setdefault(key, {})

        def stat(category: str, value=1):
            group[category] = group.get(category, 0) + value  # noqa: B023

        stat("mutations")
        if metadata.get("dropped", False):
            stat("dropped")
            if not show_dropped:
                continue
        else:
            stat("kept")
        for annotation in metadata.get("annotations", []):
            annotation_categories.add(annotation)
            stat(annotation)
        for llm_stat, value in metadata.get("llm_stats", {}).items():
            llm_categories.add(llm_stat)
            stat(llm_stat, value)
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
                    stat(category)

    category_sections = [
        ("counts", count_categories),
        ("llm", list(sorted(llm_categories))),
        ("annotations", list(sorted(annotation_categories))),
    ]
    for key, group in groups.items():
        print("=" * 40)
        for name, value in zip(group_by, key, strict=True):
            name = f"{name}: {value}"
            print(f"{name:^40}")
        if len(group_by) == 0:
            print(f"{'total':^40}")
        for section, annotation_categories in category_sections:
            if len(annotation_categories) == 0:
                continue
            section = f" {section} "
            print(f"{section:-^40}")
            for category in annotation_categories:
                count = group.get(category, 0)
                category = category + ":"
                print(f"{category:<30}{count:>10}")
