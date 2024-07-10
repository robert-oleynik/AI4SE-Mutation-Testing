import abc

import tree_sitter as ts

from ..ai.llm_result import LLMResult
from ..source import MutationTarget


class Mutation:
    def __init__(self, content: str | bytes, llm_result: LLMResult | None):
        if isinstance(content, str):
            content = content.encode()
        self.content = content
        self.llm_result = llm_result

    def map(contents: list[LLMResult]) -> list["Mutation"]:
        return [Mutation(llm_result.final, llm_result) for llm_result in contents]


class MutationGenerator(abc.ABC):
    @abc.abstractmethod
    def generate_sample_prompt(
        self, source_node: ts.Node, mutation_node: ts.Node
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def generate(self, target: MutationTarget) -> list[Mutation]:
        raise NotImplementedError


class SimpleMutationGenerator(MutationGenerator):
    @abc.abstractmethod
    def generate_prompt(self, node: ts.Node) -> str:
        raise NotImplementedError

    def generate_sample_prompt(
        self, source_node: ts.Node, mutation_node: ts.Node
    ) -> str:
        prompt = self.generate_prompt(source_node)
        indent = "    "
        for c in prompt.splitlines(False)[-1]:
            if c.isspace():
                indent += c
            else:
                break
        prompt += indent + mutation_node.child_by_field_name("body").text.decode(
            "utf-8"
        )
        return prompt


class NoMutationPossible(Exception):
    pass
