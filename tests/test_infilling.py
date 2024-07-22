import tree_sitter as ts
import tree_sitter_python as tsp

from mutator.generator.infilling import InfillingGenerator
from mutator.treesitter.python import first_capture_named


def setup(*sources: list[str]) -> ts.Node:
    lang = ts.Language(tsp.language())
    parser = ts.Parser(lang)
    return [
        first_capture_named(
            "bar",
            parser.parse(source).root_node,
            '(function_definition name: (identifier) @name (#eq? @name "bar")) @bar',
        )
        for source in sources
    ]


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
        for x in range(10):
            do_something(x)
        self.called()
        for i in range(10):
            if i == 42 * 100:
                print(i)
        return "foobar"
"""


def test_generate_prompt():
    source, mutant = setup(
        source1,
        b"""
def bar(self) -> str:
    for y in range(10):
        do_something(y)
    self.called()
    for i in range(10):
        if 2 * i == 5:
            print(i)
    return "foobar"
""",
    )
    expected = """@Decorator1
@Decorator2
class Foo:
    def __init__(self):
        "Hello, World"
        self.x = 42

    def called(self):
        "Some info"
        ...

<|fim_prefix|>    def bar(self) -> str:
        for x in range(10):
            do_something(x)
        self.called()
        for i in range(10):
            if <|fim_suffix|> == 42 * 100:
                print(i)
        return "foobar"<|fim_middle|>2 * i"""
    prompt = InfillingGenerator().generate_sample_prompt(source, mutant)
    assert prompt == expected
