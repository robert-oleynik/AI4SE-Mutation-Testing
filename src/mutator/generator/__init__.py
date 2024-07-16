from .config import GeneratorConfig
from .docstring import DocstringGenerator
from .forced_branch import ForcedBranchGenerator
from .full_body import FullBodyGenerator
from .generator import Mutation, MutationGenerator
from .infilling import InfillingGenerator
from .prompt import Prompt
from .repeat import RepeatGenerator
from .rewrite import CommentRewriteContextGenerator, CommentRewriteGenerator


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
    "CommentRewriteGenerator",
    "CommentRewriteContextGenerator",
    "DocstringGenerator",
    "ForcedBranchGenerator",
    "FullBodyGenerator",
    "GeneratorConfig",
    "GeneratorConfigNotFound",
    "GeneratorNotFound",
    "InfillingGenerator",
    "Mutation",
    "MutationGenerator",
    "RepeatGenerator",
    "Prompt",
    "configs",
    "generators",
]
