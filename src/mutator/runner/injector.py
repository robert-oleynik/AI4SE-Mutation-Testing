import collections.abc
import importlib.abc
import pathlib
import sys
import types


class MutationLoader(importlib.abc.SourceLoader):
    def __init__(self, module: str, path: pathlib.Path):
        self.module = module
        self.path = path

    def get_filename(self, fullname: str) -> pathlib.Path:
        if fullname != self.module:
            raise ImportError
        return self.path

    def get_data(self, path: pathlib.Path) -> bytes:
        if path != self.path:
            raise ImportError
        return self.path.read_bytes()


class DependencyInjector(importlib.abc.MetaPathFinder):
    def __init__(self, module: str, path: pathlib.Path):
        self.module = module
        self.path = path

    def find_spec(
            self,
            fullname: str,
            path: collections.abc.Sequence[str] | None,
            target: types.ModuleType | None = ...) -> importlib.machinery.ModuleSpec | None:
        if fullname == self.module:
            loader = MutationLoader(self.module, self.path)
            return importlib.machinery.ModuleSpec(fullname, loader)
        return None

    def install(self):
        sys.meta_path.insert(0, self)
