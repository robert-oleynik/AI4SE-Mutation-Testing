from .config import GeneratorConfig
from .doc_string_based import DocStringBasedGenerator
from .forced_branch import ForcedBranchGenerator
from .full_body_based import FullBodyBasedGenerator
from .generator import Mutation, MutationGenerator
from .identity import Identity
from .infilling import InfillingGenerator
from .repeat import RepeatGenerator


class GeneratorNotFound(Exception):
    "Raised when the specified generator is not registered"

    def __init__(self, name: str):
        self._name = name

    def message(self) -> str:
        return f"Generator '{self._name}' is not registered"


class GeneratorConfigNotFound(Exception):
    "Raised when the specified generator config is not registered"

    def __init__(self, name: str):
        self._name = name

    def message(self) -> str:
        return f"Generator config '{self._name}' is not registered"


__all__ = [
    "DocStringBasedGenerator",
    "ForcedBranchGenerator",
    "FullBodyBasedGenerator",
    "GeneratorConfig",
    "GeneratorConfigNotFound",
    "GeneratorNotFound",
    "Identity",
    "InfillingGenerator",
    "Mutation",
    "MutationGenerator",
    "RepeatGenerator",
    "configs",
    "generators",
]
