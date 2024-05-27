import mutator.ai
from ..treesitter.python import tsLang, tsParser
from ..source import MutationTarget, SourceFile
from .generator import Mutation, MutationGenerator

_tsQuery = tsLang.query("(expression_statement (string) @docstring)")


class DocStringBasedGenerator(MutationGenerator):
    def generate(self, source: SourceFile, target: MutationTarget) -> list[Mutation]:
        content = target.content(source.content)
        tree = tsParser.parse(content)
        matches = _tsQuery.matches(tree.root_node)
        if len(matches) == 0:
            return []
        docstring = matches[0][1]["docstring"]
        prompt = content[: docstring.end_byte].decode()
        results = mutator.ai.llm.prompt(prompt, True)
        return [Mutation(result.encode()) for result in results]
