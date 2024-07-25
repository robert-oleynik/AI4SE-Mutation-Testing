import re


def pattern_to_regex(pattern: str):
    return re.compile("^" + pattern.replace(".", "\\.").replace("*", ".*") + "$")
