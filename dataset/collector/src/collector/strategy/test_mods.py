import difflib
import typing

import git
import tree_sitter as ts
import tree_sitter_python as tsp

from ..sample import Sample
from ..source import compare_tree, find_py_fn_by_name
from .strategy import Strategy

_tsLang = ts.Language(tsp.language())
_tsQuery = _tsLang.query("(function_definition) @target")


def detect_targets(tree: ts.Tree) -> typing.Generator[ts.Node, None, None]:
    for _, captures in _tsQuery.matches(tree.root_node):
        yield captures["target"]


class TestMods(Strategy):
    """
    Filters all commits, which do not modify the tests. Without related issue.
    """

    def apply(self, repo: git.Repo) -> typing.Generator[Sample, None, None]:
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

                    changes = []
                    matcher = difflib.SequenceMatcher(None, a_blob, b_blob)
                    for tag, _, _, j1, j2 in matcher.get_opcodes():
                        if tag == "equal":
                            continue
                        changes.append((j1, j2))

                    a_tree = parser.parse(a_blob)
                    b_tree = parser.parse(b_blob)
                    for b_node in detect_targets(b_tree):
                        for b, e in changes:
                            if b_node.start_byte <= b and b <= b_node.end_byte:
                                break
                            if b_node.start_byte <= e and e <= b_node.end_byte:
                                break
                        else:
                            continue
                        name = b_node.child_by_field_name("name").text.decode()
                        # TODO: Check scope
                        any_a_node = None
                        for a_node in find_py_fn_by_name(a_tree.root_node, name):
                            if not compare_tree(b_node, a_node):
                                any_a_node = a_node
                        if any_a_node is not None:
                            yield Sample(
                                commit, b_node, o.b_path, b_node.text, a_node.text
                            )
