import os
import pathlib

from .generator import Mutation
from .source import MutationTarget, SourceFile


class MutationStore:
    """
    Manage the filesystem storage of all mutations.
    """

    def __init__(self, out: pathlib.Path):
        self.base = out
        self.base.mkdir(parents=True,exist_ok=True)
        self.counter = {}

    def add(self, source: SourceFile, target: MutationTarget, mutation: Mutation):
        ident = target.fullname
        path = self.base.joinpath(f"{source.module}/{ident}")
        path.mkdir(parents=True,exist_ok=True)
        if path not in self.counter:
            self.counter[path] = 0
        content = source.content[:target.begin] + \
            mutation.content + \
            source.content[target.end:]
        file = path.joinpath(f"{self.counter[path]}.py")
        file.write_bytes(content)

    def isclean(self) -> bool:
        try:
            return len(os.listdir(self.base)) == 0
        except FileNotFoundError:
            return True

    def list_mutation(self) -> list[tuple[str, str, pathlib.Path]]:
        mutations = []
        for module in os.listdir(self.base):
            module_path = self.base.joinpath(module)
            for target in os.listdir(module_path):
                target_path = module_path.joinpath(target)
                for file in os.listdir(target_path):
                    file_path = target_path.joinpath(file)
                    mutations.append((module, target, file_path))
        return mutations
