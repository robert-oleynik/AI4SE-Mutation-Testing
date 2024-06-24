import pathlib
import shutil
import traceback

import click

from ..generator import (
    CommentRewriteGenerator,
    DocStringBasedGenerator,
    ForcedBranchGenerator,
    FullBodyBasedGenerator,
    GeneratorConfig,
    GeneratorConfigNotFound,
    GeneratorNotFound,
    Identity,
    InfillingGenerator,
    RepeatGenerator,
)
from ..source import Filter, SourceFile, compare_tree
from ..store import MutationStore
from ..treesitter.python import tsParser

generators = {
    "doc_string_based": DocStringBasedGenerator(),
    "forced_branch": ForcedBranchGenerator(),
    "full_body_based": FullBodyBasedGenerator(),
    "identity": Identity(),
    "infilling": InfillingGenerator(),
    "repeat": RepeatGenerator(),
    "comment_rewrite": CommentRewriteGenerator(),
}

configs = {
    "single_result": GeneratorConfig(
        {
            "num_return_sequences": 1,
        },
        tries_per_target=1,
    ),
    "beam_search": GeneratorConfig(
        {
            "do_sample": True,
            "num_beams": 8,
            "no_repeat_ngram_size": 32,
            "num_return_sequences": 4,
        },
        tries_per_target=4,
    ),
}


@click.command()
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "mutations"),
    type=pathlib.Path,
    show_default=True,
    help="Directory used to store mutations",
)
@click.option(
    "-g",
    "--generator",
    multiple=True,
    type=click.Choice(generators.keys(), case_sensitive=False),
    default=list(generators.keys()),
    show_default=True,
    help="Specify generator used for generating mutations",
)
@click.option(
    "-c",
    "--config",
    multiple=True,
    default=list(configs.keys()),
    show_default=True,
    help="LLM configuration to use for generators",
)
@click.option(
    "-p",
    "--project",
    type=pathlib.Path,
    default=".",
    show_default=True,
    help="Path to project directory",
)
@click.option(
    "-f",
    "--filter",
    multiple=True,
    help="Specify select filter for identifying mutations",
)
@click.option(
    "-m",
    "--model",
    default="google/codegemma-1.1-2b",
    help="LLM model used to generate mutations",
)
@click.option(
    "--checkpoint", type=pathlib.Path, help="Load checkpoints instead of model"
)
@click.option(
    "-d",
    "--device",
    default="cuda:0",
    show_default=True,
    help="GPU device used to run LLM on",
)
@click.option("--no-llm", is_flag=True, help="Do not load LLM. May brake generators")
@click.option("--clean", is_flag=True, help="Regenerate all mutations")
def generate(
    out_dir,
    generator,
    config,
    project,
    filter,
    model,
    device,
    no_llm,
    clean,
    checkpoint,
):
    # foo
    if not no_llm:
        import mutator.ai.llm

        from ..ai import LLM
        from ..ai.limiter.function import FunctionLimiter

        mutator.ai.llm = LLM(device, model, [FunctionLimiter], max_new_tokens=2000)
    filters = Filter(filter)
    sourceRoot = pathlib.Path(project.joinpath("src")).resolve()
    source_files = [
        f
        for f in [
            SourceFile(sourceRoot, file, filters) for file in sourceRoot.rglob("*.py")
        ]
        if len(f.symbols) > 0
    ]

    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    store = MutationStore(out_dir)
    if not store.isclean():
        print("error: found existing mutations. use flag `--clean` to generate new.")
        return 1

    for source_file in source_files:
        for target in source_file.targets:
            target_path = f"{source_file.module}:{target.fullname}"
            counter = 0
            dropped = 0

            def status_update():
                print(
                    f"\r - {target_path:<80} [mutations: {counter} dropped: {dropped}] ",
                    end="",
                )

            status_update()
            original_tree = tsParser.parse(target.content()).root_node
            trees = [original_tree]
            try:
                for gen in generator:
                    if gen not in generators:
                        raise GeneratorNotFound(gen)
                    g = generators[gen]
                    for conf in config:
                        if conf not in configs:
                            raise GeneratorConfigNotFound(conf)
                        c = configs[conf]
                        try:
                            mutations = g.generate(target, c)
                        except Exception as e:
                            print("\nwarning: caught exception, skip")
                            traceback.print_exception(e)
                            continue
                        for mutation in mutations:
                            new_tree = tsParser.parse(mutation.content).root_node
                            if any(compare_tree(tree, new_tree) for tree in trees):
                                dropped += 1
                            else:
                                counter += 1
                                store.add(target, mutation, gen, c)
                                trees.append(new_tree)
                            status_update()
            finally:
                print()
