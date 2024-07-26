import re


class Pattern:
    def __init__(self, pattern: str):
        self.regex = re.compile(
            "^" + pattern.replace(".", "\\.").replace("*", ".*") + "$"
        )

    def matches(self, name: str) -> bool:
        return self.regex.fullmatch(name) is not None


class Filter:
    def __init__(self, patterns: list[str]):
        self.include = []
        self.exclude = []
        for pattern in patterns:
            if pattern.startswith("!"):
                self.exclude.append(Pattern(pattern[1:]))
            else:
                self.include.append(Pattern(pattern))

    def should_include(self, name: str) -> bool:
        def _match(pattern):
            return pattern.matches(name)

        return any(map(_match, self.include)) and not any(map(_match, self.exclude))
