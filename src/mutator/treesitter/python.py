import tree_sitter as ts
import tree_sitter_python as tsp

tsLang = ts.Language(tsp.language())
tsParser = ts.Parser(tsLang)


def first_capture_named(capture_name: str, node: ts.Node, query: str):
    for _, captures in tsLang.query(query).matches(node):
        for capture, node in captures.items():
            if capture == capture_name:
                return node
    return None
