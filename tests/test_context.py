import tree_sitter as ts
import tree_sitter_python as tsp

from mutator.generator.rewrite import CommentRewriteGenerator
from mutator.treesitter.context import Context
from mutator.treesitter.python import first_capture_named


def setup(source: str) -> ts.Node:
    lang = ts.Language(tsp.language())
    parser = ts.Parser(lang)
    module = parser.parse(source).root_node
    return first_capture_named(
        "bar",
        module,
        '(function_definition name: (identifier) @name (#eq? @name "bar")) @bar',
    )


source1 = b"""
@Decorator1
@Decorator2
class Foo:
    def __init__(self):
        "Hello, World"
        self.x = 42

    def another(self, a, b):
        "Hello, WOrld"
        return a + b

    def called(self):
        "Some info"
        return 42

    @Decorator3
    @Decorator4
    def bar(self) -> str:
        self.called()
        return "foobar"
"""


def test_class_header():
    node = setup(source1)
    expected_class_header = "@Decorator1\n@Decorator2\nclass Foo:\n    "
    assert Context(node).class_header() == expected_class_header


def test_generate_prompt():
    node = setup(source1)
    expected = """@Decorator1
@Decorator2
class Foo:
    def __init__(self):
        "Hello, World"
        self.x = 42

    def called(self):
        "Some info"
        ...

#    @Decorator3
#    @Decorator4
#    def bar(self) -> str:
#        self.called()
#        return "foobar"

    @Decorator3
    @Decorator4
    def bar(self) -> str:
"""
    prompt = CommentRewriteGenerator().generate_prompt(node)
    assert prompt == expected
