import tree_sitter as ts

from ..ai.transform import trim_prompt
from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class ForcedBranchGenerator(MutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        definition, indent = Context(target.node).relevant_class_definition()
        signature = target.get_signature().decode()
        results = []
        for _ in range(config.tries_per_target):
            prompt = definition + indent + target.content().decode()
            results += mutator.ai.llm.force_branch(
                prompt,
                transform_result=trim_prompt(definition + indent),
                keep_prefix_len=len(definition) + len(indent) + len(signature),
                **config.model_kwargs,
            )
        return Mutation.map(results)
