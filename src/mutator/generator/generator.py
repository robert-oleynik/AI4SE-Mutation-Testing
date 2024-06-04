import abc

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
    def generate(self, target: MutationTarget) -> list[Mutation]:
        raise NotImplementedError
