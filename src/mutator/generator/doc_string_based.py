import mutator.ai

from ..source import MutationTarget
from ..treesitter.python import tsLang, tsParser
from .generator import Mutation, MutationGenerator

_tsQuery = tsLang.query("(expression_statement (string) @docstring)")


class DocStringBasedGenerator(MutationGenerator):
    def generate(self, target: MutationTarget) -> list[Mutation]:
        content = target.content()
        tree = tsParser.parse(content)
        matches = _tsQuery.matches(tree.root_node)
        if len(matches) == 0:
            return []
        docstring = matches[0][1]["docstring"]
        prompt = content[: docstring.end_byte].decode()
        results = mutator.ai.llm.prompt(
            prompt, True, num_return_sequences=1,
            **config.model_kwargs
        )  # TODO: Use beam search
        return [Mutation(result.encode()) for result in results]
