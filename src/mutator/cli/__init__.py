from .generate import Generate
from .inspect import Inspect
from .test import Test

commands = {
        "test": Test(),
        "generate": Generate(),
        "inspect": Inspect(),
}

__all__ = [
    "Generate",
    "Test",
]
