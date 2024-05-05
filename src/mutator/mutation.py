import pathlib
import difflib

from .project import MutationTarget, SourceFile


class Mutation:
    """
    TODO
    """

    def __init__(self, source: SourceFile, target: MutationTarget, mutation: str):
        self.source = source
        self.target = target
        self.mutation = mutation

    def apply(self) -> bytes:
        return self.source.content[:self.target.begin] + \
            self.target.content(self.source.content) + \
            self.source.content[self.target.end:]


class MutationStore:
    def __init__(self, base: pathlib.Path, mutations: list[Mutation]):
        self.base = base
        self.mutations = mutations

        for i, mutation in enumerate(self.mutations):
            buildDir = base.joinpath(mutation.source.module)
            buildDir.mkdir(parents=True,exist_ok=True)
            with open(f"{buildDir}/{i}.py", "wb") as file:
                file.write(mutation.apply())
                file.close()

    def mutation_diff(self, id: int) -> str:
        source = self.mutations[id].source.content.decode().splitlines(keepends=True)
        mutation = self.mutations[id].apply().decode().splitlines(keepends=True)
        diff = difflib.unified_diff(source, mutation) 
        return '\n'.join(list(diff))

    def source_path(self, id: int) -> pathlib.Path:
        return self.base.joinpath(self.mutations[id].source.module).joinpath(f"{id}.py")
