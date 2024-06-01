from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class FullBodyBasedGenerator(MutationGenerator):
    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        prompt = "# Original version\n"
        prompt += target.content().decode()
        prompt += "\n\n# Mutated version for mutation testing\n"
        results = mutator.ai.llm.prompt(prompt, **config.model_kwargs)
        return [Mutation(result.encode()) for result in results]
