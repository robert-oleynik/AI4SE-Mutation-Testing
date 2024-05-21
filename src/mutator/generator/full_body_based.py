import mutator.ai

from ..source import MutationTarget, SourceFile
from .generator import Mutation, MutationGenerator


class FullBodyBasedGenerator(MutationGenerator):
    def generate(self, source: SourceFile, target: MutationTarget) -> list[Mutation]:
        prompt = "# Original version\n"
        prompt += target.content(source.content).decode()
        prompt += "\n\n# Mutated version for mutation testing\n"
        answer = mutator.ai.llm.prompt(prompt)
        return [Mutation(answer.encode())]
