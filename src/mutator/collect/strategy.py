import abc
import typing

import autopep8
import git
import tree_sitter as ts

from ..generator.generator import MutationGenerator


class Sample:
    def __init__(
        self,
        commit: git.Commit,
        diff: git.Diff,
        source_node: ts.Node,
        mutation_node: ts.Node,
    ):
        self.commit = commit
        self.diff = diff
        self.source_node = source_node
        self.mutation_node = mutation_node

    def to_dict(self, generator: MutationGenerator) -> dict:
        prompt = generator.generate_sample_prompt(self.source_node, self.mutation_node)
        return {
            "commit": self.commit.hexsha,
            "file": self.diff.b_path,
            "start": self.mutation_node.start_byte,
            "end": self.mutation_node.end_byte,
            "source": autopep8.fix_code(self.source_node.text.decode("utf-8")),
            "mutation": autopep8.fix_code(self.mutation_node.text.decode("utf-8")),
            "prompt": prompt,
        }


class Strategy(abc.ABC):
    @abc.abstractmethod
    def apply(self, repo: git.Repo) -> typing.Generator[Sample, None, None]:
        raise NotImplementedError
