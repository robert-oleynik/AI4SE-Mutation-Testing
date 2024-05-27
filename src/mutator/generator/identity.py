from ..source import MutationTarget
from .generator import Mutation, MutationGenerator


class Identity(MutationGenerator):
    def generate(self, target: MutationTarget) -> list[Mutation]:
        return [Mutation(target.content())]
