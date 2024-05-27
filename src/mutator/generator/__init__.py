from .generator import Mutation, MutationGenerator
from .identity import Identity
from .full_body_based import FullBodyBasedGenerator
from .doc_string_based import DocStringBasedGenerator

generators = {
        "identity": Identity(),
        "full_body_based": FullBodyBasedGenerator(),
        "doc_string_based": DocStringBasedGenerator(),
}


class GeneratorNotFound(Exception):
    "Raised when the specified generator is not registered"

    def __init__(self, name: str):
        self._name = name

    def message(self) -> str:
        return f"Generator '{self._name}' is not registered"

__all__ = [
        "MutationGenerator",
        "Mutation",
        "Identity",
        "FullBodyBasedGenerator",
        "DocStringBasedGenerator",
        "generators"
]
