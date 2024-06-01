import abc
import typing

import git

from .sample import Sample


class Strategy(abc.ABC):
    @abc.abstractmethod
    def apply(self, repo: git.Repo) -> typing.Generator[Sample, None, None]:
        raise NotImplementedError
