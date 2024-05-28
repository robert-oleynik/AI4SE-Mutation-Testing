import mutator.ai.llm

from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class RepeatGenerator(MutationGenerator):
    """
    Generate Mutations by indicating repeated source code, but forcing changes.
    """

    def generate(self, target: MutationTarget, config: GeneratorConfig) -> list[Mutation]:
        full = target.content().decode()
        name = target.get_name().decode()
        signature = target.get_signature().decode()
        query = f"<|file_separator|>{name}.py\n{full}\n<|file_separator|>{name}.py\n{signature}"
        outputs = mutator.ai.llm.prompt(query, **config.model_kwargs)

        def _encode(output):
            return f"{signature}{output}".encode()

        return [Mutation(_encode(o)) for o in outputs]
