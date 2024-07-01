from collections.abc import Callable


def identity(result: str) -> str:
    return result


def trim_prompt(prompt: str) -> Callable[[str], str]:
    prompt_len = len(prompt)

    def transform(result: str) -> str:
        return result[prompt_len:]

    return transform
