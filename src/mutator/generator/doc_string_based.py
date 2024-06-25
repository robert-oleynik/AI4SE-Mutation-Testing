import tree_sitter as ts

from ..ai.transform import trim_prompt
from ..source import MutationTarget
from ..treesitter.context import Context
from ..treesitter.python import tsLang, tsParser
from .config import GeneratorConfig
from .generator import Mutation, SimpleMutationGenerator, NoMutationPossible


class DocStringBasedGenerator(SimpleMutationGenerator):
    def _generate_prompt(self, node: ts.Node) -> tuple[str, str]:
        context = Context(node)
        docstring = context.docstring()
        if not docstring:
            raise NoMutationPossible()
        definition, indent = context.relevant_class_definition()
        to_trim = definition + indent
        prompt = to_trim + node.text[: docstring.end_byte - node.start_byte].decode()
        return prompt, to_trim

    def generate_prompt(self, node: ts.Node) -> str:
        prompt, _ = self.generate_prompt(node)
        return prompt

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        try:
            prompt, to_trim = self._generate_prompt(target.node)
        except NoMutationPossible:
            return []
        results = mutator.ai.llm.llm.prompt(
            prompt,
            transform_result=trim_prompt(to_trim),
            **config.model_kwargs,
        )
        return Mutation.map(results)
