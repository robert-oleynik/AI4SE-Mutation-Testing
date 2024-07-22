import tree_sitter as ts

from ..helper.tries import tries
from ..source import MutantTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutant, SimpleMutantGenerator


class CommentRewriteNoContextGenerator(SimpleMutantGenerator):
    """
    Tries to regenerate a mutant by commenting out the old function and prompting
    the AI to regenerate this function.
    """

    def _generate_prompt(self, node: ts.Node) -> str:
        method_context = Context(node)
        _, indent = method_context.relevant_class_definition()
        prompt = ""
        for decorator_node in method_context.decorators():
            prompt += "#" + indent + decorator_node.text.decode() + "\n"
        fn_body = indent + node.text.decode()
        for line in fn_body.splitlines(True):
            prompt += "#" + line
        prompt += "\n\n"
        for decorator_node in method_context.decorators():
            prompt += indent + decorator_node.text.decode() + "\n"
        prompt += indent
        strip_len = len(prompt)
        docstring = method_context.docstring()
        if docstring is not None:
            prompt += node.text[: docstring.end_byte - node.start_byte].decode()
        return prompt, strip_len

    def generate_prompt(self, node: ts.Node) -> str:
        prompt, _ = self._generate_prompt(node)
        return prompt

    def generate(self, target: MutantTarget, config: GeneratorConfig) -> list[Mutant]:
        import mutator.ai.llm

        prompt, strip_len = self._generate_prompt(target.node)

        def transform(result: str) -> str:
            return result[strip_len:]

        model_kwargs = {
            **config.model_kwargs,
        }

        def generate():
            return mutator.ai.llm.llm.prompt(
                prompt,
                transform_result=transform,
                **model_kwargs,
            )

        return Mutant.map(tries(config.tries_per_target, generate))


class CommentRewriteGenerator(CommentRewriteNoContextGenerator):
    """
    Tries to regenerate a mutant by commenting out the old function and prompting
    the AI to regenerate this function, while providing the surrounding
    class definition.
    """

    def generate_prompt(self, node: ts.Node) -> str:
        prompt = super().generate_prompt(node)
        method_context = Context(node)
        definition, indent = method_context.relevant_class_definition()
        return definition + prompt
