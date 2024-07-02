import json
import os
import pathlib
import typing
from dataclasses import asdict

from .generator import GeneratorConfig, Mutation
from .source import MutationTarget


class MutationStore:
    """
    Manage the filesystem storage of all mutations.
    """

    def __init__(self, out: pathlib.Path):
        self.base = out
        self.base.mkdir(parents=True, exist_ok=True)
        self.counter = {}

    def add(
        self,
        target: MutationTarget,
        mutation: Mutation,
        generator: str,
        config: GeneratorConfig,
        is_dropped: bool,
        annotations: list[str] = None,
    ):
        if annotations is None:
            annotations = []
        path = self.base / f"{target.source.module}" / target.fullname
        path.mkdir(parents=True, exist_ok=True)
        if path not in self.counter:
            self.counter[path] = 0
        else:
            self.counter[path] += 1
        content = (
            target.source.content[: target.node.start_byte]
            + mutation.content
            + target.source.content[target.node.end_byte :]
        )
        json.dump(
            {
                "dropped": is_dropped,
                "file": str(target.source.path),
                "mutation": mutation.content.decode(),
                "start": target.node.start_point,
                "end": target.node.end_point,
                "generator": generator,
                "config": asdict(config),
                "annotations": annotations,
            },
            open(path / f"{self.counter[path]}.json", "w"),
        )
        (path / f"{self.counter[path]}.py").write_bytes(content)

    def isclean(self) -> bool:
        try:
            return len(os.listdir(self.base)) == 0
        except FileNotFoundError:
            return True

    def list_mutation(
        self,
    ) -> typing.Generator[
        tuple[str, str, pathlib.Path, pathlib.Path, dict], None, None
    ]:
        for module in os.listdir(self.base):
            module_path = self.base.joinpath(module)
            if not module_path.is_dir():
                continue
            for target in os.listdir(module_path):
                target_path = module_path / target
                for file in os.listdir(target_path):
                    if file.endswith(".py"):
                        metadata = json.load(
                            open((target_path / file).with_suffix(".json"))
                        )
                        source_file = metadata["file"]
                        file_path = target_path.joinpath(file)
                        yield module, target, file_path, source_file, metadata
