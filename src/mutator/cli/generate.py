import argparse
import pathlib

import mutator.ai

from ..ai import LLM
from ..generator import GeneratorNotFound, generators
from ..source import SourceFile
from ..store import MutationStore


class Generate:
    """
    Configures and runs CLI command to generate mutations.
    """

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
                "-o", "--out-dir",
                action="store",
                type=pathlib.Path,
                help="Output directory.")
        parser.add_argument(
                "-g", "--generator",
                action="append",
                type=str,
                nargs="*",
                help = "Name of a generator to use.")
        parser.add_argument(
                "-c", "--chdir",
                action="store",
                type=pathlib.Path,
                default=pathlib.Path.cwd(),
                help="Change working directory.")
        parser.add_argument("-d", "--device", action="store")
        parser.add_argument("-m", "--model", action="store")
        parser.add_argument("--max-new-tokens", type=int, action="store")

    def run(self,
            out_dir: pathlib.Path | None,
            generator: list[str] | None,
            chdir: pathlib.Path | None,
            device: str | None,
            model: str | None,
            max_new_tokens: int,
            **other) -> int:
        if device is None:
            device = "cuda:0"
        if model is None:
            model = "google/codegemma-2b"
        mutator.ai.llm = LLM(device, model, max_new_tokens=max_new_tokens)

        if generator is None:
            generator = ["simple"]
        if chdir is None:
            chdir = pathlib.Path.cwd()
        if out_dir is None:
            out_dir = chdir.joinpath("out/mutations")

        # TODO: Allow multiple source roots
        sourceRoot = pathlib.Path(chdir.joinpath("src")).resolve()
        sourceFiles = list(filter(
            lambda s: len(s.targets) > 0,
            map(lambda p: SourceFile(sourceRoot, p), sourceRoot.rglob("*.py"))))

        store = MutationStore(out_dir)
        for gen in generator:
            if gen not in generators:
                raise GeneratorNotFound(gen)
            g = generators[gen]

            for sourceFile in sourceFiles:
                for target in sourceFile.targets:
                    for mutation in g.generate(sourceFile, target):
                        store.add(sourceFile, target, mutation)
        return 0
