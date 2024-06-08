import tree_sitter as ts

from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class Identity(MutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        return [Mutation(target.content())]
