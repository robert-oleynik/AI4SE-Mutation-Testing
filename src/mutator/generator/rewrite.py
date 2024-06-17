import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class CommentRewriteGenerator(MutationGenerator):
    """
    Tries to regenerate new mutation by comment the old function and prompt the AI to
    regenerate this function.
    """

    def generate_prompt(self, node: ts.Node) -> str:
        method_context = Context(node)
        prompt, indent = method_context.relevant_class_definition()
        for decorator_node in method_context.decorators():
            prompt += "#" + indent + decorator_node.text.decode() + "\n"
        fn_body = indent + node.text.decode()
        for line in fn_body.splitlines(True):
            prompt += "#" + line
        prompt += "\n\n"
        for decorator_node in method_context.decorators():
            prompt += indent + decorator_node.text.decode() + "\n"
        prompt += indent + method_context.fn_signature() + "\n"
        return prompt

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        prompt = self.generate_prompt(target.node)

        def transform(result: str) -> str:
            return result[len(prompt) :]

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )
        return Mutation.map(results)
