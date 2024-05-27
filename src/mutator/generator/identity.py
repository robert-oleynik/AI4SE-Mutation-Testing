from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class Identity(MutationGenerator):
    def generate(self, target: MutationTarget, config: GeneratorConfig) -> list[Mutation]:
        return [Mutation(target.content())]
