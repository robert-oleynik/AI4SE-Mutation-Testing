from ...treesitter.python import tsLang, tsParser
from .limiter import Limiter

_errQuery = tsLang.query("(ERROR)")


class FunctionLimiter(Limiter):
    def extract_result(self, result: str) -> str | None:
        source = result.encode()
        tree = tsParser.parse(source)
        root = tree.root_node
        count = len(root.children)
        if (
            root.type == "ERROR"
            or count <= 1
            or root.children[0].type != "function_definition"
        ):
            return None
        function = root.children[0]
        detected_errors = list(_errQuery.matches(function))
        if (
            len(detected_errors) > 0
            or function.child_by_field_name("body").child_count < 1
        ):
            return None
        return function.text.decode()
