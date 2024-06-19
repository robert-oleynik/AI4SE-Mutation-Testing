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
        strip_len = len(prompt) - (len(Context(target.node).fn_signature()) + 1)

        def transform(result: str) -> str:
            return result[strip_len:]

        fim_tokens = ["<|fim_middle|>", "<|fim_suffix|>", "<|fim_prefix|>"]
        fim_tokens = [
            [token]
            for token in mutator.ai.llm.tokenizer.encode(
                fim_tokens, add_special_tokens=False
            )
        ]

        model_kwargs = {
            **config.model_kwargs,
            "length_penalty": 4,
            "bad_words_ids": fim_tokens,
        }

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **model_kwargs,
        )
        return Mutation.map(results)
