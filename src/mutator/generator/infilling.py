import random

import tree_sitter as ts

from ..source import MutantTarget
from ..treesitter.context import Context
from ..treesitter.python import tsLang
from ..treesitter.tree_walker import compare
from .config import GeneratorConfig
from .generator import Mutant, MutantGenerator, NoMutantPossible

_docstring_query = tsLang.query("""
(function_definition body: (block . (expression_statement (string) @docstring)))
""")
_targets_query = tsLang.query("""
(expression) @expr
(block (_) @statement)
""")


class InfillingGenerator(MutantGenerator):
    def create_prompt(
        self, source_node: ts.Node, start_byte: int, end_byte: int, middle=""
    ):
        definition, indent = Context(source_node).relevant_class_definition()
        prefix = source_node.text[: start_byte - source_node.start_byte].decode()
        suffix = source_node.text[end_byte - source_node.start_byte :].decode()
        prompt = f"{definition}<|fim_prefix|>{indent}{prefix}"
        prompt += f"<|fim_suffix|>{suffix}<|fim_middle|>{middle}"
        return prompt, prefix, suffix

    def generate_sample_prompt(self, source_node: ts.Node, mutant_node: ts.Node) -> str:
        equal, source, mutant = compare(source_node.walk(), mutant_node.walk())
        if equal:
            raise NoMutantPossible()
        start_byte = source.start_byte if source else mutant.start_byte
        end_byte = source.end_byte if source else mutant.start_byte
        middle = mutant.text.decode() if mutant else ""
        prompt, _, _ = self.create_prompt(source_node, start_byte, end_byte, middle)
        return prompt

    def generate(self, target: MutantTarget, config: GeneratorConfig) -> list[Mutant]:
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
        return Mutant.map(results)
