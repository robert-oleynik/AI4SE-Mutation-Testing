import tree_sitter as ts

from ..helper.tries import tries
from ..source import MutantTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutant, NoMutantPossible, SimpleMutantGenerator


class DocstringGenerator(SimpleMutantGenerator):
    def _generate_prompt(self, node: ts.Node) -> tuple[str, str]:
        context = Context(node)
        docstring = context.docstring()
        if not docstring:
            raise NoMutantPossible()
        definition, indent = context.relevant_class_definition()
        to_trim = definition + indent
        prompt = to_trim + node.text[: docstring.end_byte - node.start_byte].decode()
        return prompt, to_trim

    def generate_prompt(self, node: ts.Node) -> str:
        prompt, _ = self.generate_prompt(node)
        return prompt

    def generate(self, target: MutantTarget, config: GeneratorConfig) -> list[Mutant]:
        import mutator.ai.llm
        from mutator.ai.transform import trim_prompt

        try:
            prompt, to_trim = self._generate_prompt(target.node)
        except NoMutantPossible:
            return []

        def generate():
            return mutator.ai.llm.llm.prompt(
                prompt,
                transform_result=trim_prompt(to_trim),
                **config.model_kwargs,
            )

        return Mutant.map(tries(config.tries_per_target, generate))
