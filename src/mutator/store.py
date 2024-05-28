import os
import pathlib
import typing

from .generator import Mutation
from .source import MutationTarget


class MutationStore:
    """
    Manage the filesystem storage of all mutations.
    """

    def __init__(self, out: pathlib.Path):
        self.base = out
        self.base.mkdir(parents=True, exist_ok=True)
        self.counter = {}

    def add(self, target: MutationTarget, mutation: Mutation):
        path = self.base / f"{target.source.module}" / target.fullname
        path.mkdir(parents=True, exist_ok=True)
        if path not in self.counter:
            self.counter[path] = 0
        else:
            self.counter[path] += 1
        content = (
            target.source.content[: target.begin]
            + mutation.content
            + target.source.content[target.end :]
        )
        (path / "file").write_bytes(f"{target.source.path}".encode())
        file = path / f"{self.counter[path]}.py"
        file.write_bytes(content)

    def isclean(self) -> bool:
        try:
            return len(os.listdir(self.base)) == 0
        except FileNotFoundError:
            return True

    def list_mutation(
        self,
    ) -> typing.Generator[tuple[str, str, pathlib.Path, pathlib.Path], None, None]:
        for module in os.listdir(self.base):
            module_path = self.base.joinpath(module)
            for target in os.listdir(module_path):
                target_path = module_path / target
                source_file = (target_path / "file").read_bytes().decode()
                for file in os.listdir(target_path):
                    if file.endswith(".py"):
                        file_path = target_path.joinpath(file)
                        yield module, target, file_path, source_file
