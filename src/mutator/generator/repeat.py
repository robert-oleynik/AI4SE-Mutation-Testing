import mutator.ai.llm

from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class RepeatGenerator(MutationGenerator):
    """
    Generate Mutations by indicating repeated source code, but forcing changes.
    """

    def generate(self, target: MutationTarget, config: GeneratorConfig) -> list[Mutation]:
        name = target.node.child_by_field_name("name").text.decode()
        params = target.node.child_by_field_name("parameters").text.decode()
        full = target.node.text.decode()
        query = f"""<|file_separator|>{name}.py
        {full}
        <|file_separator|>{name}.py
        def {name}{params}:
        """
        outputs = mutator.ai.llm.prompt(query, **config.model_kwargs)

        def _encode(output):
            return f"def {name}{params}:\n{output}".encode()

        return [Mutation(_encode(o)) for o in outputs]
