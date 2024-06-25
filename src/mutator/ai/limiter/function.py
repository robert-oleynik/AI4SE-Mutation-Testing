from ...treesitter.python import tsLang, tsParser
from .limiter import Limiter

_errQuery = tsLang.query("(ERROR)")


class FunctionLimiter(Limiter):
    def is_too_long(self, result: str) -> bool:
        source = result.encode()
        tree = tsParser.parse(source)
        root = tree.root_node
        detected_errors = list(_errQuery.matches(root))
        if root.type == "ERROR" or len(detected_errors) > 0:
            # let the LLM generate more code until its at least partially valid
            return False
        assert root.type == "module"
        count = len(root.children)
        result = count > 1 or (
            count == 1 and root.children[0].type not in ["ERROR", "function_definition"]
        )
        return result
