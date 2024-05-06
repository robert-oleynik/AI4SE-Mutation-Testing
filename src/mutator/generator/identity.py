from ..source import MutationTarget, SourceFile
from .generator import Mutation, MutationGenerator


class Identity(MutationGenerator):
    def generate(self, source: SourceFile, target: MutationTarget) -> list[Mutation]:
        return [Mutation(target.content(source.content))]
