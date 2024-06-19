import tree_sitter as ts
import tree_sitter_python as tsp

from mutator.source import compare_tree

lang = ts.Language(tsp.language())
parser = ts.Parser(lang)


def test_same():
    source = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    a_node = parser.parse(source).root_node
    b_node = parser.parse(source).root_node
    assert compare_tree(a_node, b_node)


def test_modified_comment():
    source_a = b"""
def foo(a: int, b: int) -> int:
    # foo
    return a * b + a
"""
    source_b = b"""
def foo(a: int, b: int) -> int:
    # bar
    return a * b + a
"""
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert compare_tree(a_node, b_node)


def test_modified_doc_comment():
    source_a = b"""
def foo(a: int, b: int) -> int:
    "foo"
    return a * b + a
"""
    source_b = b"""
def foo(a: int, b: int) -> int:
    "bar"
    return a * b + a
"""
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert compare_tree(a_node, b_node)


def test_rename():
    source_a = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    source_b = b"""
def fooa(a: int, b: int) -> int:
    return a * b + a
"""
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert compare_tree(a_node, b_node)


def test_diff():
    source_a = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    source_b = b"""
def foo(a: int, b: int) -> int:
    return a + b + a
"""
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert not compare_tree(a_node, b_node)


if __name__ == "__main__":
    test_same()
