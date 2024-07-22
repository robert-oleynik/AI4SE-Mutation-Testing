from .config import GeneratorConfig
from .docstring import DocstringGenerator
from .generator import Mutant, MutantGenerator
from .infilling import InfillingGenerator
from .prefix import PrefixGenerator
from .prompt import Prompt
from .rewrite import CommentRewriteGenerator, CommentRewriteNoContextGenerator


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
    "CommentRewriteNoContextGenerator",
    "DocstringGenerator",
    "PrefixGenerator",
    "GeneratorConfig",
    "GeneratorConfigNotFound",
    "GeneratorNotFound",
    "InfillingGenerator",
    "Mutant",
    "MutantGenerator",
    "Prompt",
    "configs",
    "generators",
]
