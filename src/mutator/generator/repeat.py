import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class RepeatGenerator(MutationGenerator):
    """
    Generate Mutations by indicating repeated source code, but forcing changes.
    """

    def generate_prompt(self, node: ts.Node) -> str:
        context = Context(node)
        n = context.get_parent_class()
        signature = context.fn_signature()
        return (
            "<|file_separator|>\n"
            + n.text.decode()
            + "\n<|file_separator|>\n"
            + signature
            + "\n"
        )

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        prompt = self.generate_prompt(target.node)

        def transform(result: str) -> str:
            offset = len(prompt.splitlines(True)[:-2].join())
            return result[offset:]

        results = mutator.ai.llm.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )
        return Mutation.map(results)
