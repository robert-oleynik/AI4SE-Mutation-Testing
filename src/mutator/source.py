import pathlib
import re
import typing

import tree_sitter as ts

from .treesitter.python import tsLang, tsParser

_tsFunctionQuery = tsLang.query("""
(function_definition) @target
""")


class InvalidNodeType(Exception):
    "Raised when an expected node type does not match received one"


class MissingIdentifier(Exception):
    "Raised when a tree sitter expects an identifier but no one was found"


class Symbol:
    def __init__(self, content: bytes, node: ts.Node):
        if node.type != "function_definition":
            raise InvalidNodeType()
        self.node = node
        self.name = ""

        n = self.node
        while n.type != "module":
            if n.type == "function_definition" or n.type == "class_definition":
                ident = n.child_by_field_name("name")
                if ident is not None and ident.type == "identifier":
                    self.name = ident.text.decode() + "." + self.name
                else:
                    raise MissingIdentifier()
            n = n.parent
        self.name = self.name[:-1]


class Filter:
    class Matcher:
        def __init__(self, f: str):
            module, symbol = f.split(":")

            def _toRegex(f):
                return re.compile(f.replace(".", "\\.").replace("*", "[^\\.]*") + "$")

            self.module = _toRegex(module)
            self.symbol = _toRegex(symbol)

        def match(self, module: str, symbol: str) -> bool:
            return (
                self.module.fullmatch(module) is not None
                and self.symbol.fullmatch(symbol) is not None
            )

    def __init__(self, filters: list[str]):
        self.include = []
        self.exclude = []
        for f in filters:
            if f.startswith("!"):
                self.exclude.append(self.Matcher(f[1:]))
            else:
                self.include.append(self.Matcher(f))

    def match(self, module: str, symbol: str) -> bool:
        def _match(m):
            return m.match(module, symbol)

        return any(map(_match, self.include)) and not any(map(_match, self.exclude))


class SourceFile:
    """
    Stores all information associated with a python source file.
    """

    def __init__(self, root: pathlib.Path, path: pathlib.Path, filter: Filter):
        self.path = path.relative_to(root)

        self.module = self.path.stem
        for parent in self.path.parents:
            if parent != parent.parent:
                self.module = f"{parent.name}.{self.module}"
        if self.module.endswith(".__init__"):
            self.module = self.module[:-9]

        self.content = path.read_bytes()
        self.tree = tsParser.parse(self.content)
        self.symbols = []
        lines = self.content.splitlines(keepends=True)
        for _, captures in _tsFunctionQuery.matches(self.tree.root_node):
            symbol = Symbol(self.content, captures["target"])
            if filter.match(self.module, symbol.name):
                self.symbols.append(symbol)
        self.targets = [MutationTarget(self, lines, symbol) for symbol in self.symbols]


class MutationTarget:
    """
    Stores offset/positions of target identifier and content.
    """

    def __init__(self, source: SourceFile, lines: list[bytes], symbol: Symbol):
        self.source = source
        self.node = symbol.node
        self.fullname = symbol.name

    def content(self) -> bytes:
        return self.source.content[self.node.start_byte : self.node.end_byte]

    def get_name(self) -> bytes:
        return self.node.child_by_field_name("name").text

    def get_signature(self) -> bytes:
        body = self.node.child_by_field_name("body")
        return self.source.content[self.node.start_byte : body.start_byte]


class PairTreeWalker:
    def __init__(self, a_node: ts.Node, b_node: ts.Node):
        self.a = a_node
        self.b = b_node
        self.a_idents = []
        self.b_idents = []
        self.a_walk = self.a.walk()
        self.b_walk = self.b.walk()

    def __walker_skip_comments(self, walker) -> bool:
        while True:
            if walker.node.type != "comment":
                if (
                    walker.node.type != "expression_statement"
                    or walker.node.child(0).type != "string"
                ):
                    break
            if not walker.goto_next_sibling():
                return False
        return True

    def update(self) -> bool:
        if self.a_walk.node.type != self.b_walk.node.type:
            return False
        if self.a_walk.node.type == "identifier":
            a_node = self.a_walk.node
            p1_node = a_node.parent
            p2_node = p1_node.parent
            if (
                p1_node.type == "attribute"
                and p1_node.child_by_field_name("attribute").id == a_node.id
                and p2_node.type == "call"
            ):
                return self.a_walk.node.text == self.b_walk.node.text
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
        if a:
            a = self.__walker_skip_comments(self.a_walk)
        b = self.b_walk.goto_first_child()
        if b:
            b = self.__walker_skip_comments(self.b_walk)
        return a, b

    def goto_next_sibling(self) -> tuple[bool, bool]:
        a = self.a_walk.goto_next_sibling()
        if a:
            a = self.__walker_skip_comments(self.a_walk)
        b = self.b_walk.goto_next_sibling()
        if b:
            b = self.__walker_skip_comments(self.b_walk)
        return a, b

    def goto_parent(self) -> tuple[bool, bool]:
        a = self.a_walk.goto_parent()
        b = self.b_walk.goto_parent()
        return a, b


def _compare_tree_rec(walker: PairTreeWalker, depth: int = 0) -> bool:
    a, b = walker.goto_first_child()
    # print(" " * depth + walker.a_walk.node.type, walker.b_walk.node.type)
    if a != b:
        return False
    elif not a:
        return True
    while True:
        if not walker.update():
            return False
        if not _compare_tree_rec(walker, depth=depth + 1):
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
    query = tsLang.query(query_str)
    for _, captures in query.matches(root):
        if "target" in captures:
            yield captures["target"]
