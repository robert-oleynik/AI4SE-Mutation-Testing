from .config import GeneratorConfig
from .doc_string_based import DocStringBasedGenerator
from .full_body_based import FullBodyBasedGenerator
from .generator import Mutation, MutationGenerator
from .identity import Identity
from .repeat import RepeatGenerator

generators = {
    "identity": Identity(),
    "full_body_based": FullBodyBasedGenerator(),
    "doc_string_based": DocStringBasedGenerator(),
    "repeat": RepeatGenerator(),
}

configs = {
    "single_result": GeneratorConfig({
        "num_return_sequences": 1,
    }),
    "beam_search": GeneratorConfig({
        "do_sample": True,
        "num_beams": 4,
        "no_repeat_ngram_size": 32,
    }),
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
    "generators",
    "configs",
]
