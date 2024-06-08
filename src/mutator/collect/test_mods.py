import difflib
import typing

import git
import tree_sitter as ts
import tree_sitter_python as tsp

from ..source import compare_tree
from ..treesitter.node import upgrade_to_ty
from .strategy import Sample, Strategy

_tsLang = ts.Language(tsp.language())
_tsQuery = _tsLang.query("(function_definition) @target")


def detect_targets(tree: ts.Tree) -> typing.Generator[ts.Node, None, None]:
    for _, captures in _tsQuery.matches(tree.root_node):
        yield captures["target"]


def _source_nodes(
    matcher: difflib.SequenceMatcher, a_tree: ts.Tree, b_tree: ts.Tree
) -> typing.Generator[tuple[ts.Node, ts.Node], None, None]:
    matches = set()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        a_node = a_tree.root_node.descendant_for_byte_range(i1, i2)
        b_node = b_tree.root_node.descendant_for_byte_range(j1, j2)
        a_node = upgrade_to_ty(a_node, "function_definition")
        b_node = upgrade_to_ty(b_node, "function_definition")
        if a_node.type != "function_definition" or b_node.type != "function_definition":
            continue
        if (a_node, b_node) in matches:
            continue
        matches.add((a_node, b_node))
        yield a_node, b_node


class TestMods(Strategy):
    """
    Filters all commits, which do not modify the tests. Without related issue.
    """

    def apply(self, repo: git.Repo) -> typing.Generator[dict, None, None]:
        parser = ts.Parser(_tsLang)
        for commit in repo.iter_commits(paths="tests"):
            if len(commit.parents) > 1 or len(commit.parents) == 0:
                # NOTE: Ignore merge commits and initial commit
                continue
            for o in commit.parents[0].diff(commit):
                if o.change_type == "A" or o.change_type == "D":
                    continue
                if not o.b_path.startswith("tests") and o.b_path.endswith(".py"):
                    a_blob = o.a_blob.data_stream.read()
                    b_blob = o.b_blob.data_stream.read()

                    a_tree = parser.parse(a_blob)
                    b_tree = parser.parse(b_blob)
                    matcher = difflib.SequenceMatcher(None, a_blob, b_blob)
                    for a_node, b_node in _source_nodes(matcher, a_tree, b_tree):
                        if not compare_tree(a_node, b_node):
                            continue
                        # TODO: Generate Prompt
                        yield Sample(commit, o, a_node, b_node)
                        yield Sample(commit, o, b_node, a_node)
