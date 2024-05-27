import argparse
import pathlib
import shutil

import mutator.ai
import mutator.generator

from ..ai import LLM
from ..ai.limiter.function import FunctionLimiter
from ..generator import GeneratorNotFound
from ..source import Filter, SourceFile
from ..store import MutationStore


class Generate:
    """
    Configures and runs CLI command to generate mutations.
    """

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "-o",
            "--out-dir",
            action="store",
            type=pathlib.Path,
            help="Output directory.",
        )
        parser.add_argument("--clean", action="store_true", default=False)
        parser.add_argument(
            "-g",
            "--generators",
            default="full_body_based",
            type=str,
            help="Comma-separated list of names of generators to use.",
        )
        parser.add_argument(
            "--num-mutations",
            default=1,
            type=int,
            help="Number of mutations per (LLM) based generator",
        )
        parser.add_argument(
            "-c",
            "--chdir",
            action="store",
            type=pathlib.Path,
            default=pathlib.Path.cwd(),
            help="Change working directory.",
        )
        parser.add_argument("-d", "--device", action="store")
        parser.add_argument(
            "-m", "--model", action="store", default="google/codegemma-2b"
        )
        parser.add_argument("--skip-ai", action="store_true")
        parser.add_argument("filters", nargs="*", type=str)

    def run(
        self,
        out_dir: pathlib.Path | None,
        generators: str,
        chdir: pathlib.Path | None,
        device: str | None,
        model: str | None,
        filters: list[str],
        skip_ai: bool,
        clean: bool,
        num_mutations: int,
        **other,
    ) -> int:
        if device is None:
            device = "cuda:0"
        if not skip_ai:
            mutator.ai.llm = LLM(
                device,
                model,
                [FunctionLimiter],
                max_new_tokens=2000,
                num_return_sequences=num_mutations,
            )

        generator_names = generators.split(",")
        if chdir is None:
            chdir = pathlib.Path.cwd()
        if out_dir is None:
            out_dir = chdir.joinpath("out/mutations")

        f = Filter(filters)

        # TODO: Allow multiple source roots
        sourceRoot = pathlib.Path(chdir.joinpath("src")).resolve()
        sourceFiles = [
            SourceFile(sourceRoot, file, f) for file in sourceRoot.rglob("*.py")
        ]
        sourceFiles = list(filter(lambda f: len(f.symbols) > 0, sourceFiles))

        if clean and out_dir.exists():
            shutil.rmtree(out_dir)
        store = MutationStore(out_dir)
        if not store.isclean():
            print(
                "error: found existing mutations. use flag `--clean` to generate new ones."
            )
            return 1
        for gen in generator_names:
            if gen not in mutator.generator.generators:
                raise GeneratorNotFound(gen)
            g = mutator.generator.generators[gen]

            print(f"Generating with '{gen}'")
            for sourceFile in sourceFiles:
                for target in sourceFile.targets:
                    targetPath = f"{sourceFile.module}:{target.fullname}"
                    print(f" - {targetPath}", end="\r")
                    counter = 0
                    for mutation in g.generate(sourceFile, target):
                        counter += 1
                        store.add(sourceFile, target, mutation)
                        print(f" - {targetPath:<100} [mutations: {counter}]", end="\r")
                    print()
        return 0
