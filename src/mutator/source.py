import pathlib

import tree_sitter as ts
import tree_sitter_python as tsp

_tsLang = ts.Language(tsp.language(), "python")
_tsParser = ts.Parser()
_tsParser.set_language(_tsLang)

_tsDecoratorQuery = _tsLang.query("""
((decorated_definition
    (decorator
        (identifier) @ident.builtin)
    definition: (_) @target)
    (#eq? @ident.builtin "Mutate"))
((decorated_definition
    (decorator
        (attribute) @ident.builtin)
    definition: (_) @target)
    (#any-of? @ident.builtin "mutator.helper.Mutate" "mutator.helper.decorator.Mutate"))
""")

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
            length -= len(line[eo+1:])
            break
    return offset, offset+length


class MutationTarget:
    """
    Stores offset/positions of target identifier and content.
    """

    def __init__(self, lines: list[bytes], node: ts.Node):
        self.node = node
        self.idbegin, self.idend = 0, 0
        if self.node.type == "function_definition":
            ident = self.node.child_by_field_name("name")
            if ident is not None and ident.type == "identifier":
                self.idbegin, self.idend = _map_tsnode_pos_to_byte_range(lines, ident)
        self.begin, self.end = _map_tsnode_pos_to_byte_range(lines, self.node)

    def ident(self, content: bytes) -> bytes:
        return content[self.idbegin:self.idend-1]

    def content(self, content: bytes) -> bytes:
        return content[self.begin:self.end]

class SourceFile:
    """
    Stores all information associated with a python source file.
    """

    def __init__(self, root: pathlib.Path, path: pathlib.Path):
        self.path = path.relative_to(root)

        self.module = self.path.stem
        for parent in self.path.parents:
            if parent != parent.parent:
                self.module = f"{parent.name}.{self.module}"
        if self.module.endswith(".__init__"):
            self.module = self.module[:-9]

        self.targets = []
        self.content = path.read_bytes()
        lines = self.content.splitlines(keepends=True)
        self.tree = _tsParser.parse(self.content)
        for _, captures in _tsDecoratorQuery.matches(self.tree.root_node):
            if "target" in captures and isinstance(captures["target"], ts.Node):
                self.targets.append(MutationTarget(lines, captures["target"]))
