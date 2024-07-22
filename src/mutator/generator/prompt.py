import autopep8
import tree_sitter as ts

from ..helper.tries import tries
from ..source import MutantTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutant, SimpleMutantGenerator

_prompt = """
# Context
You are an AI Agent, part of the Software Quality Assurance Team. Your task is to modify
code in ways that will test the robustness of the test suite. You will be provided with
a function block to introduce a mutant that must:

1. Be syntactically correct.
2. Avoid trivial modifications, such as:
    * Adding unnecessary logging, comments, or environment variables.
    * Importing unused modules.
    * Altering function, class, or method signatures.
    * Adding parameters to functions, classes, or methods.
    * Changing names of variables, functions, classes, or methods.
3. Represent realistic code changes that could occur during development, such as:
    * Altering constants and literals.
    * Tweaking condition checks and logical operators.
    * Changing control flow constructs.
    * Modifying error handling mechanisms.
4. Focus on critical areas such as error handling, boundary conditions,
   and logical branches. Ensure these areas are robustly tested.
""".strip()


class Prompt(SimpleMutantGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        context = Context(node)
        prompt = _prompt + "\n\n"
        # TODO: Remove indent from function body
        prompt += "Source:\n" + autopep8.fix_code(node.text.decode()) + "\n\n"
        prompt += "Mutant:\n" + context.fn_signature() + "\n"
        return prompt

    def generate(self, target: MutantTarget, config: GeneratorConfig) -> list[Mutant]:
        import mutator.ai.llm

        indent = target.node.start_point[1]
        prompt = self.generate_prompt(target.node)
        strip_len = len(prompt) - (len(Context(target.node).fn_signature()) + 1)

        def transform(result: str) -> str:
            return result[strip_len:]

        results = mutator.ai.llm.llm.prompt(
            prompt, transform_result=transform, **config.model_kwargs
        )

        def add_indent(input: str) -> str:
            return "".join(
                [
                    " " * indent + line if line != "\n" else "\n"
                    for line in input.splitlines(True)
                ]
            )[indent:]

        def generate():
            return [Mutant(add_indent(result.final), result) for result in results]

        return tries(config.tries_per_target, generate)
