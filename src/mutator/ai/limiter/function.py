from ...treesitter.python import tsParser
from .limiter import Limiter


class FunctionLimiter(Limiter):
    def is_too_long(self, result: str) -> bool:
        source = result.encode()
        source_lines = source.splitlines()
        tree = tsParser.parse(source)
        root = tree.root_node
        if root.type == "ERROR":
            # let the LLM generate more code until its at least partially valid
            return False
        assert root.type == "module"
        count = len(root.children)
        return (
            count > 1
            or count == 1
            and root.children[0].type not in ["ERROR", "function_definition"]
        )
