import random

import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.python import token_nodes
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class InfillingGenerator(MutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        body = target.node.child_by_field_name("body")
        tokens = list(token_nodes(body))
        if tokens[0].type == "string":
            # skip docstring
            tokens = tokens[1:]
        start, end = sorted(
            random.sample(tokens, 2), key=lambda token: token.start_byte
        )
        content = target.source.content
        prefix = content[target.node.start_byte : start.start_byte].decode()
        suffix = content[end.start_byte : target.node.end_byte].decode()
        prompt = f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"

        def transform(result: str) -> str:
            return prefix + result[len(prompt) :] + suffix

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )
        return Mutation.map(results)
