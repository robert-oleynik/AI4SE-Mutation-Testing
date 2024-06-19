import tree_sitter as ts
import tree_sitter_python as tsp

# from mutator.generator.rewrite import CommentRewriteGenerator, write_class_header


def setup(source: str) -> ts.Node:
    lang = ts.Language(tsp.language())
    parser = ts.Parser(lang)
    return parser.parse(source).root_node


# source1 = b"""
# @Decorator1
# @Decorator2
# class Foo:
#    def __init__(self):
#        "Hello, World"
#        pass
#
#    def another(self, a, b):
#        "Hello, WOrld"
#        return a + b
#
#    @Decorator3
#    @Decorator4
#    def bar(self) -> str:
#        return "foobar"
# """


# def test_write_class_header():
#    node = setup(source1)
#    expected_class_header = "@Decorator1\n@Decorator2\nclass Foo:\n    "
#    node = node.child(0)
#    assert write_class_header(node) == expected_class_header


# def test_generate_prompt():
#    node = (
#        setup(source1)
#        .child(0)
#        .child_by_field_name("definition")
#        .child_by_field_name("body")
#        .child(2)
#        .child_by_field_name("definition")
#    )
#    expected = """@Decorator1
# @Decorator2
# class Foo:
#    def __init__(self):
#        "Hello, World"
#        ...
#
#    def another(self, a, b):
#        "Hello, WOrld"
#        ...
#
#    @Decorator3
#    @Decorator4
#    def bar(self) -> str:
#        return "foobar"
#
#    @Decorator3
#    @Decorator4
#    def bar(self) -> str:
# """
#    prompt = CommentRewriteGenerator().generate_prompt(node)
#    assert prompt == expected
