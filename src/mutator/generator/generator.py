import abc

from ..source import MutationTarget, SourceFile


class Mutation:
    def __init__(self, content: bytes):
        self.content = content

class MutationGenerator(abc.ABC):
    @abc.abstractmethod
    def generate(self, source: SourceFile, target: MutationTarget) -> list[Mutation]:
        raise NotImplementedError
