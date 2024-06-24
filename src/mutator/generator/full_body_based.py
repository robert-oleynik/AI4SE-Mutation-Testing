import tree_sitter as ts

from ..ai.transform import trim_prompt
from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, SimpleMutationGenerator


class FullBodyBasedGenerator(SimpleMutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        definition, indent = Context(target.node).relevant_class_definition()
        prompt = definition + indent + "# Original version\n"
        prompt += indent + target.content().decode()
        prompt += f"\n\n{indent}# Mutated version for mutation testing\n{indent}"
        results = mutator.ai.llm.llm.prompt(
            prompt,
            transform_result=trim_prompt(prompt),
            **config.model_kwargs,
        )
        return Mutation.map(results)
