import json
import pathlib


class Result:
    def __init__(self, path: pathlib.Path | None = None):
        if path is not None:
            data = json.loads(path.read_bytes())
            if "modules" not in data:
                raise Exception("missing key 'modules' in result file")
            self.modules = data["modules"]
        else:
            self.modules = {}

    def write(self, path: pathlib.Path):
        data = {"modules": self.modules}
        path.write_bytes(json.dumps(data).encode())

    def read(path: pathlib.Path):
        if not path.is_file():
            return None
        return json.load(open(path))["modules"]

    def insert(
        self,
        module: str,
        symbol: str,
        mutant: str,
        file: pathlib.Path,
        source: pathlib.Path,
        is_caught: bool,
        is_syntax_error: bool,
        is_timeout: bool,
        output: str,
    ):
        if module not in self.modules:
            self.modules[module] = {}
        if symbol not in self.modules[module]:
            self.modules[module][symbol] = {}
        if mutant not in self.modules[module][symbol]:
            self.modules[module][symbol][mutant] = {
                "file": f"{file}",
                "caught": is_caught,
                "syntax_error": is_syntax_error,
                "source": source,
                "timeout": is_timeout,
                "output": output,
            }
