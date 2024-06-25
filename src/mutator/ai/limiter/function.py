from ...treesitter.python import tsParser
from .limiter import Limiter


class FunctionLimiter(Limiter):
    def is_too_long(self, result: str, prompt_len: int) -> bool:
        tree = tsParser.parse(result.encode("utf-8"))
        walker = tree.walk()
        while walker.node.type != "function_definition":
            if not walker.goto_first_child_for_byte(prompt_len - 1):
                return False  # NOTE: Invalid Syntax/Not a function
        return walker.goto_next_sibling()
