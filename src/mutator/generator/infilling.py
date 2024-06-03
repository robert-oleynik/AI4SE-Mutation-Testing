import random
from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class InfillingGenerator(MutationGenerator):
    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        content = target.content().decode()
        signature_len = len(target.get_signature().decode())
        start = random.randint(signature_len, len(content) - 1)
        end = random.randint(start + 1, len(content))
        prefix = content[:start]
        suffix = content[end:]
        prompt = f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"

        def transform(result: str) -> str:
            return prefix + result[len(prompt):] + suffix

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )
        return [Mutation(result.encode()) for result in results]
