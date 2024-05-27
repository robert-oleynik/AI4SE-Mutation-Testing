import pathlib
import re

import tree_sitter as ts

from .treesitter.python import tsLang, tsParser

_tsFunctionQuery = tsLang.query("""
(function_definition) @target
""")


class InvalidNodeType(Exception):
    "Raised when an expected node type does not match received one"


class MissingIdentifier(Exception):
    "Raised when a tree sitter expects an identifier but no one was found"


def _map_tsnode_pos_to_byte_range(lines: list[bytes], node: ts.Node) -> tuple[int, int]:
    bl, bo = node.start_point
    el, eo = node.end_point
    offset = 0
    length = 0
    for i, line in enumerate(lines):
        if i < bl:
            offset += len(line)
        elif i == bl:
            offset += bo
            length += len(line[bo:])
        else:
            length += len(line)
        if el == i:
            length -= len(line[eo + 1 :])
            break
    return offset, offset + length


class Symbol:
    def __init__(self, content: bytes, lines: list[bytes], node: ts.Node):
        if node.type != "function_definition":
            raise InvalidNodeType()
        lines = content.splitlines(True)
        self.node = node
        self.name = ""

        n = self.node
        while n.type != "module":
            if n.type == "function_definition" or n.type == "class_definition":
                ident = n.child_by_field_name("name")
                if ident is not None and ident.type == "identifier":
                    begin, end = _map_tsnode_pos_to_byte_range(lines, ident)
                    self.name = content[begin : end - 1].decode() + "." + self.name
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


class MutationTarget:
    """
    Stores offset/positions of target identifier and content.
    """

    def __init__(self, lines: list[bytes], symbol: Symbol):
        self.node = symbol.node
        self.fullname = symbol.name
        self.begin, self.end = _map_tsnode_pos_to_byte_range(lines, self.node)

    def content(self, content: bytes) -> bytes:
        return content[self.begin : self.end]


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
            symbol = Symbol(self.content, lines, captures["target"])
            if filter.match(self.module, symbol.name):
                self.symbols.append(symbol)
        self.targets = [MutationTarget(lines, symbol) for symbol in self.symbols]
