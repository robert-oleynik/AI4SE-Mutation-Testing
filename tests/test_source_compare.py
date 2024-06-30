import tree_sitter as ts
import tree_sitter_python as tsp

from mutator.treesitter.tree_walker import compare

lang = ts.Language(tsp.language())
parser = ts.Parser(lang)


def test_same():
    source = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    a_tree = parser.parse(source)
    b_tree = parser.parse(source)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert equal
    assert a_node is None
    assert b_node is None


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
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert equal
    assert a_node is None
    assert b_node is None


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
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert equal
    assert a_node is None
    assert b_node is None


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
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert equal
    assert a_node is None
    assert b_node is None


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
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert not equal
    assert a_node is not None
    assert b_node is not None
    assert a_node.type == "string_content"
    assert b_node.type == "string_content"


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
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert not equal
    assert a_node is not None
    assert b_node is not None
    assert a_node.type == "identifier"
    assert b_node.type == "identifier"


def test_rename1():
    source_a = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    source_b = b"""
def fooa(a: int, b: int) -> int:
    return a * b + a
"""
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert equal
    assert a_node is None
    assert b_node is None


def test_rename2():
    source_a = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    source_b = b"""
def foo(b: int, a: int) -> int:
    return b * a + b
"""
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert equal
    assert a_node is None
    assert b_node is None


def test_diff():
    source_a = b"""
def foo(a: int, b: int) -> int:
    return a * b + a
"""
    source_b = b"""
def foo(a: int, b: int) -> int:
    return a + b + a
"""
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert not equal
    assert a_node.text.decode() == "*"
    assert b_node.text.decode() == "+"


def test_conditional():
    source_a = b"""
def foo() -> int:
    if True:
        a = 1
    else:
        a = 1
    return a
"""
    source_b = b"""
def foo() -> int:
    if True:
        a = 1
    else:
        b = 1
    return a
"""
    a_tree = parser.parse(source_a)
    b_tree = parser.parse(source_b)
    equal, a_node, b_node = compare(a_tree.walk(), b_tree.walk())
    assert not equal
    assert a_node.text.decode() == "a"
    assert b_node.text.decode() == "b"


if __name__ == "__main__":
    test_same()
