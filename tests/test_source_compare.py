import tree_sitter as ts
import tree_sitter_python as tsp

from mutator.source import compare_tree
from mutator.treesitter.python import first_capture_named

lang = ts.Language(tsp.language())
parser = ts.Parser(lang)


def test_same():
    source = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    a_node = parser.parse(source).root_node
    b_node = parser.parse(source).root_node
    assert compare_tree(a_node, b_node) == (True, None, None)


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


def test_removed_doc_comment():
    source_a = b"""
def foo(a: int, b: int) -> int:
    "foo"
    return a * b + a
"""
    source_b = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert compare_tree(a_node, b_node)


def test_modified_str():
    source_a = b"""
def foo(a: int, b: int) -> int:
    s = "foo"
    return a * b + a
"""
    source_b = b"""
def foo(a: int, b: int) -> int:
    s = "bar"
    return a * b + a
"""
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert compare_tree(a_node, b_node)


def test_change_function_call_rename():
    source_a = b"""
def foo(self, l):
    item = l.pop()
    return self.foo(item)
    """
    source_b = b"""
def foo(self, l):
    item = l.popitem()
    return self.foo(item)
    """
    a_node = parser.parse(source_a).root_node
    b_node = parser.parse(source_b).root_node
    assert not compare_tree(a_node, b_node)


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
    assert compare_tree(a_node, b_node) == (True, None, None)


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
    a_diff = first_capture_named("node", a_node, '"*" @node')
    b_diff = first_capture_named("node", b_node, '(binary_operator left: (identifier) @left (#eq? @left "a") "+" @node)')
    assert compare_tree(a_node, b_node) == (False, a_diff, b_diff)


if __name__ == "__main__":
    test_same()
