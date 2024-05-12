from .limiter import Limiter
from ...treesitter.python import tsParser


class FunctionLimiter(Limiter):
    def __init__(self):
        self.tree = tsParser.parse(b"")

    def is_too_long(self, result: str) -> bool:
        source = result.encode()
        source_lines = source.splitlines()
        old_root = self.tree.root_node
        self.tree.edit(
            start_byte=old_root.end_byte,
            old_end_byte=old_root.end_byte,
            new_end_byte=len(source),
            start_point=old_root.end_point,
            old_end_point=old_root.end_point,
            new_end_point=(len(source_lines), len(source_lines[-1]))
        )
        self.tree = tsParser.parse(source, self.tree)
        root = self.tree.root_node
        if root.type == "ERROR":
            # let the LLM generate more code until its at least partially valid
            return False
        assert root.type == "module"
        count = len(root.children)
        return count > 1 or count == 1 and root.children[0].type not in ["ERROR", "function_definition"]
