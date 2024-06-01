import typing

import tree_sitter as ts
import tree_sitter_python as tsp

_tsLang = ts.Language(tsp.language())


class PairTreeWalker:
    def __init__(self, a_node: ts.Node, b_node: ts.Node):
        self.a = a_node
        self.b = b_node
        self.a_idents = []
        self.b_idents = []
        self.a_walk = self.a.walk()
        self.b_walk = self.b.walk()

    def update(self) -> bool:
        if self.a_walk.node.type != self.b_walk.node.type:
            return False
        if self.a_walk.node.type == "identifier":
            a_ident = self.a_walk.node.text
            try:
                a_i = self.a_idents.index(a_ident)
            except ValueError:
                a_i = len(self.a_idents)
                self.a_idents.append(a_ident)
            b_ident = self.b_walk.node.text
            try:
                b_i = self.b_idents.index(b_ident)
            except ValueError:
                b_i = len(self.b_idents)
                self.b_idents.append(b_ident)
            return a_i == b_i
        return True

    def done(self) -> bool:
        return self.a_walk.node == self.a and self.b_walk.node == self.b

    def goto_first_child(self) -> tuple[bool, bool]:
        a = self.a_walk.goto_first_child()
        b = self.b_walk.goto_first_child()
        return a, b

    def goto_next_sibling(self) -> tuple[bool, bool]:
        a = self.a_walk.goto_next_sibling()
        b = self.b_walk.goto_next_sibling()
        return a, b

    def goto_parent(self) -> tuple[bool, bool]:
        a = self.a_walk.goto_parent()
        b = self.b_walk.goto_parent()
        return a, b


def _compare_tree_rec(walker: PairTreeWalker) -> bool:
    a, b = walker.goto_first_child()
    if a != b:
        return False
    elif not a:
        return True
    while True:
        if not walker.update():
            return False
        if not _compare_tree_rec(walker):
            return False

        a, b = walker.goto_next_sibling()
        if a != b:
            return False
        if not a:
            break
    a, b = walker.goto_parent()
    return a == b


def compare_tree(a_node: ts.Node, b_node: ts.Node) -> bool:
    """
    Compares two tree nodes by walking/comparing their syntax tree.
    """
    walker = PairTreeWalker(a_node, b_node)
    return _compare_tree_rec(walker)


def find_py_fn_by_name(
    root: ts.Node, name: str
) -> typing.Generator[ts.Node, None, None]:
    query_str = f"""(
  (function_definition name: (identifier) @name.builtin) @target
    (#eq? @name.builtin "{name}")
)"""
    query = _tsLang.query(query_str)
    for _, captures in query.matches(root):
        if "target" in captures:
            yield captures["target"]
