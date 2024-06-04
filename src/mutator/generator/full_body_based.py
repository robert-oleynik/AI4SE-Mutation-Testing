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
        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=trim_prompt(prompt),
            **config.model_kwargs,
        )
        return Mutation.map(results)
