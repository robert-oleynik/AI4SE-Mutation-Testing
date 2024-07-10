import random

import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from ..treesitter.python import tsLang
from ..treesitter.tree_walker import compare
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator, NoMutationPossible

_docstring_query = tsLang.query("""
(function_definition body: (block . (expression_statement (string) @docstring)))
""")
_targets_query = tsLang.query("""
(expression) @expr
(block (_) @statement)
""")


class InfillingGenerator(MutationGenerator):
    def create_prompt(
        self, source_node: ts.Node, start_byte: int, end_byte: int, middle=""
    ):
        definition, indent = Context(source_node).relevant_class_definition()
        prefix = source_node.text[: start_byte - source_node.start_byte].decode()
        suffix = source_node.text[end_byte - source_node.start_byte :].decode()
        prompt = f"{definition}<|fim_prefix|>{indent}{prefix}"
        prompt += f"<|fim_suffix|>{suffix}<|fim_middle|>{middle}"
        return prompt, prefix, suffix

    def generate_sample_prompt(
        self, source_node: ts.Node, mutation_node: ts.Node
    ) -> str:
        equal, source, mutation = compare(source_node.walk(), mutation_node.walk())
        if equal:
            raise NoMutationPossible()
        start_byte = source.start_byte if source else mutation.start_byte
        end_byte = source.end_byte if source else mutation.start_byte
        middle = mutation.text.decode() if mutation else ""
        prompt, _, _ = self.create_prompt(source_node, start_byte, end_byte, middle)
        return prompt

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        body = target.node.child_by_field_name("body")
        docstring_matches = _docstring_query.matches(target.node)
        target_matches = _targets_query.matches(body)
        exclude = set()
        targets = set()
        for matches, ranges in [
            (docstring_matches, exclude),
            (target_matches, targets),
        ]:
            for _, match in matches:
                for _, node in match.items():
                    ranges.add(node.byte_range)
        targets.difference_update(exclude)
        targets = list(targets)
        results = []
        for start_byte, end_byte in random.sample(
            targets, min(config.tries_per_target, len(targets))
        ):
            prompt, prefix, suffix = self.create_prompt(
                target.node, start_byte, end_byte
            )

            def transform(result: str) -> str:
                return prefix + result[len(prompt) :] + suffix  # noqa: B023

            results += mutator.ai.llm.llm.prompt(
                prompt,
                transform_result=transform,
                **config.model_kwargs,
            )
        return Mutation.map(results)
