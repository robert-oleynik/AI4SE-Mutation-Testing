from ..collect.sample import Sample
from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class RepeatGenerator(MutationGenerator):
    """
    Generate Mutations by indicating repeated source code, but forcing changes.
    """

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        full = target.content().decode()
        signature = target.get_signature().decode()
        prompt = f"<|file_separator|>\n{full}\n<|file_separator|>\n{signature}"

        def transform(result: str) -> str:
            return signature + result[len(prompt):]

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )

        return [Mutation(result.encode()) for result in results]

    def format(sample: Sample) -> str:
        source = sample.source
        mutation = sample.mutation
        return f"<|file_separator|>\n{source}\n<|file_separator|>\n{mutation}"
