import tree_sitter as ts
import tree_sitter_python as tsp

tsLang = ts.Language(tsp.language())
tsParser = ts.Parser(tsLang)


def token_nodes(root_node: ts.Node) -> list[ts.Node]:
    index = 1
    cursor = root_node.walk()
    while True:
        cursor.goto_descendant(index)
        token = cursor.node
        if token == root_node:
            break
        if (token.child_count == 0 and token.type not in ["string_start", "string_content", "string_end"]) or token.type == "string":
            yield token
        index += 1
