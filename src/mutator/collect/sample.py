import pathlib
import typing

import autopep8
import git
import tree_sitter as ts


class Sample:
    def __init__(
        self,
        commit: git.Commit,
        node: ts.Node,
        path: pathlib.Path,
        source: bytes,
        mutation: bytes,
    ):
        self.commit = commit
        self.node = node
        self.source = source
        self.path = path
        self.mutation = mutation

    def build(self) -> typing.Any:
        start, _ = self.node.start_point
        end, _ = self.node.end_point
        return {
            "commit": self.commit.hexsha,
            "file": self.path,
            "start": start,
            "end": end,
            "source": autopep8.fix_code(self.source.decode("utf-8")),
            "mutation": autopep8.fix_code(self.mutation.decode("utf-8")),
        }
