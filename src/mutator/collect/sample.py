import typing

import autopep8


class Sample:
    def __init__(
        self,
        commit: str,
        path: str,
        start: int,
        end: int,
        source: str,
        mutation: str,
    ):
        self.commit = commit
        self.source = autopep8.fix_code(source)
        self.start = start
        self.end = end
        self.path = path
        self.mutation = autopep8.fix_code(mutation)

    def build(self) -> typing.Any:
        return {
            "commit": self.commit,
            "file": self.path,
            "start": self.start,
            "end": self.end,
            "source": self.source,
            "mutation": self.mutation,
        }
