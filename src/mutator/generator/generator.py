import abc

from ..source import MutationTarget


class Mutation:
    def __init__(self, content: bytes):
        self.content = content

class MutationGenerator(abc.ABC):
    @abc.abstractmethod
    def generate(self, target: MutationTarget) -> list[Mutation]:
        raise NotImplementedError
