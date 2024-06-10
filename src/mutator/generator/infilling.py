import random
from ..source import MutationTarget
from ..treesitter.python import tsLang
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator

_tsQuery = tsLang.query("""
(function_definition body: (block . (expression_statement (string) @docstring)))
(expression) @expr
(block (_) @statement)
""")

class InfillingGenerator(MutationGenerator):
    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        matches = _tsQuery.matches(target.node)
        exclude = set()
        ranges = set()
        for _, match in matches:
            for name, node in match.items():
                if name == "docstring":
                    exclude.add(node.byte_range)
                else:
                    ranges.add(node.byte_range)
        ranges.difference_update(exclude)
        start, end = random.choice(list(ranges))
        content = target.source.content
        prefix = content[target.node.start_byte : start].decode()
        suffix = content[end : target.node.end_byte].decode()
        prompt = f"<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"

        def transform(result: str) -> str:
            return prefix + result[len(prompt):] + suffix

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )
        return Mutation.map(results)
