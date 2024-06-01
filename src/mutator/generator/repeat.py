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
        query = f"<|file_separator|>\n{full}\n<|file_separator|>\n{signature}"
        outputs = mutator.ai.llm.prompt(query, **config.model_kwargs)

        def _encode(output):
            return f"{signature}{output}".encode()

        return [Mutation(_encode(o)) for o in outputs]

    def format(sample: Sample) -> str:
        source = sample.source
        mutation = sample.mutation
        return f"<|file_separator|>\n{source}\n<|file_separator|>\n{mutation}"
