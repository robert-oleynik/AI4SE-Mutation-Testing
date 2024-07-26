import csv
import math
import pathlib
import sys
from collections import Counter

import click

from ..helper.pattern import pattern_to_regex
from ..helper.timed import timed
from ..result import Result
from ..store import MutantStore


@click.command(
    help="Display stats produced during testing. Expects `test` to be run before."
)
@click.option(
    "-o",
    "--out",
    type=pathlib.Path,
    default=pathlib.Path("out", "mutants"),
    show_default=True,
    help="Path to mutant directories or a csv file that was "
    + "previously exported by this command.",
)
@click.option(
    "--show-dropped",
    is_flag=True,
    default=False,
    show_default=True,
    help="Include stats of dropped mutants.",
)
@click.option(
    "-g",
    "--group-by",
    type=click.Choice(["model_or_checkpoint", "generator", "config_name"]),
    multiple=True,
    default=[],
    help="Attributes by which to group the statistics. "
    + "Specify none to get a total across all mutants.",
)
@click.option(
    "-m",
    "--merge",
    multiple=True,
    default=[],
    help="Merge multiple categories into one. "
    + "Format: new_category=old_category_1,old_category_2,old_category_3",
)
@click.option(
    "-c",
    "--show-category",
    multiple=True,
    default=["count:*", "llm_stat:*", "annotation:*"],
)
@click.option(
    "-f",
    "--format",
    default="table",
    type=click.Choice(["table", "csv", "bar_chart", "pie_chart"]),
    show_default=True,
    help="Specify output format.",
)
@click.option(
    "-p",
    "--save-plot",
    default=None,
    type=pathlib.Path,
    show_default=True,
    help="If format is a type of plot, save the plot to this file.",
)
@timed
def stats(out, show_dropped, group_by, merge, show_category, format, save_plot):
    groups = {}
    all_categories = set(
        [
            "count:" + category
            for category in [
                "mutants",
                "dropped",
                "kept",
                "missed",
                "caught",
                "syntax_error",
                "timeout",
            ]
        ]
    )
    if out.suffix == ".csv":
        with open(out) as out_file:
            header, *rows = csv.reader(out_file)
        for row in rows:

            def find_key(name: str):
                index = header.index(name)
                if index < 0:
                    print(
                        "The specified csv file does not contain",
                        f"the group-by key {name}, aborting.",
                    )
                    sys.exit(1)
                return row[index]  # noqa: B023

            key = tuple(find_key(key_name) for key_name in group_by)
            group = groups.setdefault(key, Counter())
            for category, value in zip(header, row, strict=True):
                try:
                    value = int(value)
                except ValueError:
                    continue
                all_categories.add(category)
                group.update({category: value})
    else:
        store = MutantStore(out)
        test_result = Result.read(out / "test-result.json")
        for module, target, path, _, metadata in store.list_mutants():
            key = tuple(metadata.get(key_name, "unknown") for key_name in group_by)
            group = groups.setdefault(key, Counter())

            def stat(category: str, value=1):
                all_categories.add(category)
                group.update({category: value})  # noqa: B023

            stat("count:mutants")
            if metadata.get("dropped", False):
                stat("count:dropped")
                if not show_dropped:
                    continue
            else:
                stat("count:kept")
            for annotation in metadata.get("annotations", []):
                stat("annotation:" + annotation)
            for llm_stat, value in metadata.get("llm_stats", {}).items():
                stat("llm_stat:" + llm_stat, value)
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
                        stat("count:" + category)

    for spec in merge:
        new_category, old_categories = spec.split("=", maxsplit=1)
        old_categories = old_categories.split(",")
        for group in groups.values():
            group[new_category] = sum(group[category] for category in old_categories)
        all_categories -= set(old_categories)
        all_categories.add(new_category)

    regexes = [pattern_to_regex(pattern) for pattern in show_category]
    shown_categories = [
        category
        for regex in regexes
        for category in sorted(
            category
            for category in all_categories
            if regex.fullmatch(category) is not None
        )
    ]
    if format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(
            [
                *group_by,
                *shown_categories,
            ]
        )
        for key, group in groups.items():
            values = [group[category] for category in shown_categories]
            writer.writerow([*key, *values])
        return
    if format == "table":
        for key, group in groups.items():
            print("=" * 40)
            for name, value in zip(group_by, key, strict=True):
                name = f"{name}: {value}"
                print(f"{name:^40}")
            if len(group_by) == 0:
                print(f"{'total':^40}")
            last_section = None
            for category in shown_categories:
                section, category_name = category.split(":", maxsplit=1)
                if len(category_name) == 0:
                    continue
                if section != last_section:
                    last_section = section
                    section = f" {section} "
                    print(f"{section:-^40}")
                count = group[category]
                category_name = category_name + ":"
                print(f"{category_name:<30}{count:>10}")
        return
    if format in ["bar_chart", "pie_chart"]:
        import matplotlib.pyplot as plt

        groups = list(sorted(groups.items()))

        def key_label(key: tuple) -> list[str]:
            return "/".join(key_shorthand(key_part) for key_part in key)

        labels = [category.split(":", maxsplit=1)[1] for category in shown_categories]
        if format == "bar_chart":
            figure, axes = plt.subplots()
            bottom = [0] * len(groups)
            for category in shown_categories:
                bar_labels = [key_label(key) for key, _ in groups]
                heights = [group[category] for _, group in groups]
                axes.bar(bar_labels, heights, width=0.5, bottom=bottom)
                for index, height in enumerate(heights):
                    bottom[index] += height
            axes.set_ylim(bottom=0, top=max(*bottom) * 1.05)
            plt.legend(
                labels,
                loc="upper left",
                bbox_to_anchor=(1, 1),
                reverse=True,
            )
        elif format == "pie_chart":
            num_charts = len(groups)
            num_rows = math.floor(math.sqrt(num_charts))
            num_columns = math.ceil(num_charts / num_rows)
            figure, group_axes = plt.subplots(num_rows, num_columns)
            group_axes = group_axes.flatten()
            for index, ((key, group), axes) in enumerate(
                zip(groups, group_axes, strict=False)
            ):
                axes.pie([group[category] for category in shown_categories])
                axes.set_title(key_label(key))
                if index == num_columns - 1:
                    axes.legend(
                        labels=labels,
                        loc="upper left",
                        bbox_to_anchor=(1, 1),
                        reverse=True,
                    )
            for axes in group_axes[num_charts:]:
                axes.axis("off")
        figure.dpi = 300
        plt.subplots_adjust(right=0.8)
        if save_plot is None:
            plt.show()
        else:
            aspect = 4 / 3
            scale = 1.2
            plt.tight_layout(rect=(0, 0, aspect * scale, scale))
            plt.savefig(save_plot, bbox_inches="tight")


shorthands = {
    # models
    "google/codegemma-1.1-2b": "2b",
    "google/codegemma-7b": "7b",
    # generators
    "comment_rewrite": "crn",
    "comment_rewrite_context": "crc",
    "docstring": "ds",
    "infilling": "if",
    "prefix": "pf",
    # configs
    "beam_search": "bs_d",
    "beam_search_cold": "bs_c",
    "beam_search_hot": "bs_h",
    "multi_sample": "ms_d",
    "multi_sample_cold": "ms_c",
    "multi_sample_hot": "ms_h",
}


def key_shorthand(key: str) -> str:
    try:
        return shorthands[key]
    except KeyError:
        return key
