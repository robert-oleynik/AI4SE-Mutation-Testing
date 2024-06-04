import abc
import typing

import git


class Strategy(abc.ABC):
    @abc.abstractmethod
    def apply(self, repo: git.Repo) -> typing.Generator[dict, None, None]:
        raise NotImplementedError
