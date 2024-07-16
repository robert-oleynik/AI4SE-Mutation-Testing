import tree_sitter as ts

from ..helper.tries import tries
from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class PrefixGenerator(MutationGenerator):
    def generate_sample_prompt(
        self, source_node: ts.Node, mutation_node: ts.Node
    ) -> str:
        definition, indent = Context(mutation_node).relevant_class_definition()
        return definition + indent + mutation_node.text.decode()

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm
        from mutator.ai.transform import trim_prompt

        context = Context(target.node)
        definition, indent = context.relevant_class_definition()
        signature = target.get_signature().decode()
        docstring = context.docstring()
        docstring_len = len(docstring.text.decode()) if docstring else 0

        def generate():
            prompt = definition + indent + target.content().decode()
            return mutator.ai.llm.llm.prompt_with_random_prefix(
                prompt,
                transform_result=trim_prompt(definition + indent),
                keep_prefix_len=len(definition)
                + len(indent)
                + len(signature)
                + docstring_len,
                **config.model_kwargs,
            )

        return Mutation.map(tries(config.tries_per_target, generate))
