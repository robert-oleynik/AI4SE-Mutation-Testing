import logging
import pathlib

import tree_sitter as ts
import tree_sitter_python as tsp

tsLang = ts.Language(tsp.language(), "python")
tsParser = ts.Parser()
tsParser.set_language(tsLang)

tsDecoratorQuery = tsLang.query("""
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

class MutationTarget:
    def __init__(self, b: int, e: int):
        self.begin = b
        self.end = e

    def content(self, content: bytes) -> bytes:
        return content[self.begin:self.end]


def into_mutation_target(
        lines: list[bytes],
        begin: tuple[int, int],
        end: tuple[int, int]) -> MutationTarget:
    bl, bo = begin
    el, eo = end
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
    return MutationTarget(offset, offset+length)


class SourceFile:
    """
    Stores and manages all mutation targets of a source file.
    """

    def __init__(self, path: pathlib.Path):
        self.path = path
        self.targets = []
        with open(path, "rb") as file:
            self.content = file.read()
            lines = self.content.splitlines(keepends=True)
            tree = tsParser.parse(self.content)
            for _, captures in tsDecoratorQuery.matches(tree.root_node):
                if "target" in captures and isinstance(captures["target"], ts.Node):
                    target = into_mutation_target(lines,
                        captures["target"].start_point,
                        captures["target"].end_point)
                    bl, bo = captures["target"].start_point
                    el, eo = captures["target"].end_point
                    logging.debug("  target: %d:%d to %d:%d", bl, bo, el, eo)
                    self.targets.append(target)


class Project:
    """
    Use to manage and extract information about a python project.
    """

    def __init__(self, dir: pathlib.Path):
        self.projectDir = dir

    def scan_files(self) -> list[SourceFile]:
        sources = []
        paths = pathlib.Path(self.projectDir.joinpath("src")).rglob("*.py")
        for file in paths:
            logging.debug("source file: %s", file)
            sources.append(SourceFile(file))
        return sources

    def log_info(self):
        logging.info("project directory: %s", self.projectDir)
