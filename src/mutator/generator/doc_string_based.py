from ..source import MutationTarget
from ..treesitter.python import tsLang, tsParser
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator

_tsQuery = tsLang.query("(expression_statement (string) @docstring)")


class DocStringBasedGenerator(MutationGenerator):
    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        content = target.content()
        tree = tsParser.parse(content)
        matches = _tsQuery.matches(tree.root_node)
        if len(matches) == 0:
            return []
        docstring = matches[0][1]["docstring"]
        prompt = content[: docstring.end_byte].decode()
        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=identity,
            **config.model_kwargs,
        )
        return [Mutation(result.encode()) for result in results]
