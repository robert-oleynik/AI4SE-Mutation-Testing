import pathlib
import shutil

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
from ..source import Filter, SourceFile
from ..store import MutationStore

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
        }
    ),
    "beam_search": GeneratorConfig(
        {
            "do_sample": True,
            "num_beams": 8,
            "no_repeat_ngram_size": 32,
            "num_return_sequences": 4,
        }
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
    "-d",
    "--device",
    default="cuda:0",
    show_default=True,
    help="GPU device used to run LLM on",
)
@click.option("--no-llm", is_flag=True, help="Do not load LLM. May brake generators")
@click.option("--clean", is_flag=True, help="Regenerate all mutations")
def generate(out_dir, generator, config, project, filter, model, device, no_llm, clean):
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
            print(f" - {target_path}", end="")
            counter = 0
            try:
                for gen in generator:
                    if gen not in generators:
                        raise GeneratorNotFound(gen)
                    g = generators[gen]
                    for conf in config:
                        if conf not in configs:
                            raise GeneratorConfigNotFound(conf)
                        c = configs[conf]
                        for mutation in g.generate(target, c):
                            counter += 1
                            store.add(target, mutation)
                            print(
                                f"\r - {target_path:<80} [mutations: {counter}] ",
                                end="",
                            )
            finally:
                print()
