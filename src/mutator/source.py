import pathlib
import typing

import tree_sitter as ts

from .helper.pattern import Filter
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
            if filter.should_include(f"{self.module}:{symbol.name}"):
                self.symbols.append(symbol)
        self.targets = [MutantTarget(self, lines, symbol) for symbol in self.symbols]


class MutantTarget:
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
