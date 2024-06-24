import random

import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from ..treesitter.python import tsLang
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator

_docstring_query = tsLang.query("""
(function_definition body: (block . (expression_statement (string) @docstring)))
""")
_targets_query = tsLang.query("""
(expression) @expr
(block (_) @statement)
""")

class InfillingGenerator(MutationGenerator):
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        body = target.node.child_by_field_name("body")
        docstring_matches = _docstring_query.matches(target.node)
        target_matches = _targets_query.matches(body)
        exclude = set()
        targets = set()
        for matches, ranges in [(docstring_matches, exclude), (target_matches, targets)]:
            for _, match in matches:
                for name, node in match.items():
                    ranges.add(node.byte_range)
        targets.difference_update(exclude)
        targets = list(targets)
        content = target.source.content
        definition, indent = Context(target.node).relevant_class_definition()
        results = []
        for start, end in random.sample(targets, min(config.tries_per_target, len(targets))):
            prefix = content[target.node.start_byte : start].decode()
            suffix = content[end : target.node.end_byte].decode()
            prompt = f"{definition}<|fim_prefix|>{indent}{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"

            def transform(result: str) -> str:
                return prefix + result[len(prompt) :] + suffix

            results += mutator.ai.llm.llm.prompt(
                prompt,
                transform_result=transform,
                **config.model_kwargs,
            )
        return Mutation.map(results)
