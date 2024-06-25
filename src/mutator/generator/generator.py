import abc

import tree_sitter as ts

from ..source import MutationTarget


class Mutation:
    def __init__(self, content: str | bytes):
        if isinstance(content, str):
            content = content.encode()
        self.content = content

    def map(contents: list[str | bytes]) -> list["Mutation"]:
        return [Mutation(content) for content in contents]


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
