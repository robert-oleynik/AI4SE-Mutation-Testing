import pathlib
import re
import typing

import git
import tree_sitter as ts

pull_requests = re.compile(r"!\d+")


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
            "source": self.source.decode(),
            "mutation": self.mutation.decode(),
        }
