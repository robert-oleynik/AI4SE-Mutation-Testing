import difflib

import tree_sitter as ts
import tree_sitter_python as tsp

from mutator.collect.test_mods import _source_nodes

source1 = b"""
# A foo func
def foo():
    return "bar"
"""

source2 = b"""
# A baz func
def foo():
    return "baz"
"""


def test_():
    lang = ts.Language(tsp.language())
    parser = ts.Parser(lang)

    matcher = difflib.SequenceMatcher(None, source1, source2)
    for a_node, b_node in _source_nodes(
        matcher, parser.parse(source1), parser.parse(source2)
    ):
        assert a_node.type == "function_definition"
        assert b_node.type == "function_definition"
