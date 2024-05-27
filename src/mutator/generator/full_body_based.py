import mutator.ai

from ..source import MutationTarget
from .generator import Mutation, MutationGenerator


class FullBodyBasedGenerator(MutationGenerator):
    def generate(self, target: MutationTarget) -> list[Mutation]:
        prompt = "# Original version\n"
        prompt += target.content().decode()
        prompt += "\n\n# Mutated version for mutation testing\n"
        results = mutator.ai.llm.prompt(prompt, num_return_sequences=1)
        return [Mutation(result.encode()) for result in results]
