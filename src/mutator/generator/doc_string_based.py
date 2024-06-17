import tree_sitter as ts

from ..ai.transform import trim_prompt
from ..source import MutationTarget
from ..treesitter.context import Context
from ..treesitter.python import tsLang, tsParser
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class DocStringBasedGenerator(MutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        context = Context(target.node)
        docstring = context.docstring()
        if not docstring:
            return []
        definition, indent = context.relevant_class_definition()
        content = target.content()
        prompt = definition + indent + content[: docstring.end_byte].decode()
        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=trim_prompt(definition + indent),
            **config.model_kwargs,
        )
        return Mutation.map(results)
