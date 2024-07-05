import pathlib
import shutil
import traceback

import click

from ..ai.llm_stats import LLMStats
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
    Prompt,
    RepeatGenerator,
)
from ..source import Filter, SourceFile
from ..store import MutationStore
from ..treesitter.python import tsParser
from ..treesitter.tree_walker import compare

generators = {
    "doc_string_based": DocStringBasedGenerator(),
    "forced_branch": ForcedBranchGenerator(),
    "full_body_based": FullBodyBasedGenerator(),
    "identity": Identity(),
    "infilling": InfillingGenerator(),
    "repeat": RepeatGenerator(),
    "comment_rewrite": CommentRewriteGenerator(),
    "prompt": Prompt(),
}

configs = {
    "single_result": GeneratorConfig(
        {
            "num_return_sequences": 1,
            "max_new_tokens": 4096,
        },
        tries_per_target=1,
    ),
    "beam_search": GeneratorConfig(
        {
            "do_sample": True,
            "num_beams": 8,
            "no_repeat_ngram_size": 32,
            "num_return_sequences": 4,
            "max_new_tokens": 4096,
        },
        tries_per_target=4,
    ),
    "experimental": GeneratorConfig(
        {
            "do_sample": True,
            "num_beams": 4,
            "num_return_sequences": 4,
            "max_new_tokens": 2048,
        },
        tries_per_target=1,
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

        from ..ai.limiter.function import FunctionLimiter
        from ..ai.llm import LLM

        mutator.ai.llm.llm = LLM(device, model, [FunctionLimiter])
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

    num_targets = sum(len(source_file.targets) for source_file in source_files)
    target_index = 0

    for source_file in source_files:
        for target in source_file.targets:
            target_path = f"{source_file.module}:{target.fullname}"
            counter = 0
            dropped = 0
            target_index += 1
            generator_index = 0

            def status_update():
                print(
                    f"\r[{target_index:>{len(str(num_targets))}}/{num_targets}]",  # noqa: B023
                    f"{target_path:<80}",  # noqa: B023
                    f"[generators: {generator_index}/{len(generator)}",  # noqa: B023
                    f"mutations: {counter}",  # noqa: B023
                    f"dropped: {dropped}] ",  # noqa: B023
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
                    generator_index += 1
                    for conf in config:
                        if conf not in configs:
                            raise GeneratorConfigNotFound(conf)
                        c = configs[conf]
                        if not no_llm:
                            mutator.ai.llm.llm.reset_stats()
                        try:
                            mutations = g.generate(target, c)
                        except Exception as e:
                            print("\nwarning: caught exception, skip")
                            traceback.print_exception(e)
                            continue
                        for mutation in mutations:
                            new_tree = tsParser.parse(mutation.content).root_node
                            is_dropped = any(
                                compare(tree.walk(), new_tree.walk(), False)[0]
                                for tree in trees
                            )
                            llm_stats = (
                                LLMStats() if no_llm else mutator.ai.llm.llm.stats
                            )
                            store.add(target, mutation, gen, c, is_dropped, llm_stats)
                            if is_dropped:
                                dropped += 1
                            else:
                                counter += 1
                                trees.append(new_tree)
                            status_update()
            finally:
                print()
