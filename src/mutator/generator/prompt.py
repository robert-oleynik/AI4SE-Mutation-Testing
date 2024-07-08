import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, SimpleMutationGenerator

_prompt = """
# Context
You are an AI Agent, part of the Software Quality Assurance Team. Your task is to modify code in ways that will test the robustness of the test suite. You will be provided with a function block to introduce a mutation that must:

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
4. Focus on critical areas such as error handling, boundary conditions, and logical branches. Ensure these areas are robustly tested.
""".strip()


class Prompt(SimpleMutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        context = Context(node)
        prompt = _prompt + "\n\n"
        # TODO: Remove indent from function body
        prompt += "Source:\n" + node.text.decode() + "\n\n"
        prompt += "Mutation:\n" + context.fn_signature() + "\n"
        return prompt

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        prompt = self.generate_prompt(target.node)
        strip_len = len(prompt) - (len(Context(target.node).fn_signature()) + 1)

        def transform(result: str) -> str:
            return result[strip_len:]

        results = mutator.ai.llm.prompt(
            prompt, transform_result=transform, **config.model_kwargs
        )
        return Mutation.map(results)
