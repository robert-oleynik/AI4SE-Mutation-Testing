import collections.abc
import importlib.abc
import importlib.machinery
import logging
import pathlib
import sys
import types

from .mutation import MutationStore


class MutationLoader(importlib.abc.SourceLoader):
    def __init__(self, store: MutationStore, id: int):
        self.store = store
        self.id = id

    def get_filename(self, fullname: str) -> pathlib.Path:
        if fullname != self.store.mutations[self.id].source.module:
            raise ImportError
        return self.store.source_path(self.id)

    def get_data(self, path: pathlib.Path) -> bytes:
        if path != self.store.source_path(self.id):
            raise ImportError
        return self.store.mutations[self.id].apply()

class DependencyInjector(importlib.abc.MetaPathFinder):
    """
    Used to replace sources with mutated source files, while executing tests.
    """

    def __init__(self, store: MutationStore):
        self.store = store
        self.current = -1


    def find_spec(self,
                  fullname: str,
                  path: collections.abc.Sequence[str] | None,
                  target: types.ModuleType | None = ...,
            ) -> importlib.machinery.ModuleSpec | None:
        if fullname == self.store.mutations[self.current].source.module:
            logging.debug("load module: %s", fullname)
            loader = MutationLoader(self.store, self.current)
            return importlib.machinery.ModuleSpec(fullname, loader)
        return None

    def next_mutation(self) -> bool:
        if self.current >= 0:
            module = self.store.mutations[self.current].source.module
            if module in sys.modules:
                logging.debug("unload mutation for %s", module)
                del sys.modules[module]
            importlib.import_module(module)
        self.current += 1
        return self.current < len(self.store.mutations)

    def install(self):
        """
        Add this object sys.meta_path finder with highest precedence.
        """
        sys.meta_path.insert(0, self)

    def uninstall(self):
        """
        Remove all dependency injectors from meta path finders.
        """
        toRemove = []
        for i, finder in enumerate(sys.meta_path):
            if isinstance(finder, DependencyInjector):
                toRemove.append(i)

        for i in reversed(toRemove):
            del sys.meta_path[i]

    def current_diff(self) -> str:
        return self.store.mutation_diff(self.current)
