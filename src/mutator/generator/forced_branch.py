import tree_sitter as ts

from ..ai.transform import trim_prompt
from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class ForcedBranchGenerator(MutationGenerator):
    def generate_sample_prompt(self, source_node: ts.Node, mutation_node: ts.Node) -> str:
        definition, indent = Context(mutation_node).relevant_class_definition()
        return definition + indent + mutation_node.text.decode()

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        context = Context(target.node)
        definition, indent = context.relevant_class_definition()
        signature = target.get_signature().decode()
        docstring = context.docstring()
        docstring_len = len(docstring.text.decode()) if docstring else 0
        results = []
        for _ in range(config.tries_per_target):
            prompt = definition + indent + target.content().decode()
            results += mutator.ai.llm.llm.force_branch(
                prompt,
                transform_result=trim_prompt(definition + indent),
                keep_prefix_len=len(definition) + len(indent) + len(signature) + docstring_len,
                **config.model_kwargs,
            )
        return Mutation.map(results)
