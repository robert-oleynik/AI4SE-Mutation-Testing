from ..ai import llm
from ..source import MutationTarget
from .generator import Mutation, MutationGenerator


class Simple(MutationGenerator):
    def _query(self, prompt: str) -> str:
        answer = llm.prompt(prompt)
        return (answer
                .strip()
                .removeprefix("<bos>")
                .removesuffix("<eos>")
                .strip()
                .removesuffix("<|file_separator|>")
                .strip())

    def generate(self, source: SourceFile, target: MutationTarget) -> list[Mutation]:
        prompt = "# Original version\n"
        prompt += target.content(source.content).decode()
        prompt += "\n\n# Mutated version for mutation testing\n"
        answer = self._query(prompt)
        return [Mutation(answer[len(prompt):])]
