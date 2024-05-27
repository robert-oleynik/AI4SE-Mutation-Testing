import mutator.ai.llm

from ..source import MutationTarget, SourceFile
from .generator import Mutation, MutationGenerator


class RepeatGenerator(MutationGenerator):
    """
    Generate Mutations by indicating repeated source code, but forcing changes.
    """

    def __init__(
        self,
        num_beams: int = 4,
        no_repeat_ngram_size: int = 32,
        do_sample: bool = True,
    ):
        self.num_beams = num_beams
        self.no_repeat_ngram_size = no_repeat_ngram_size
        self.do_smaple = do_sample

    def generate(self, source: SourceFile, target: MutationTarget) -> list[Mutation]:
        name = target.node.child_by_field_name("name").text.decode()
        params = target.node.child_by_field_name("parameters").text.decode()
        full = target.node.text.decode()
        query = f"""<|file_separator|>{name}.py
        {full}
        <|file_separator|>{name}.py
        def {name}{params}:
        """
        outputs = mutator.ai.llm.prompt(
            query,
            False,
            num_beams=self.num_beams,
            no_repeat_ngram_size=self.no_repeat_ngram_size,
            do_sample=self.do_smaple,
        )

        def _encode(output):
            return f"def {name}{params}:\n{output}".encode()

        return [Mutation(_encode(o)) for o in outputs]
