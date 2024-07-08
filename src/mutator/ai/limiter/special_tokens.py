from .limiter import Limiter


class SpecialTokensLimiter(Limiter):
    def __init__(self, special_tokens: list[str]) -> None:
        self.special_tokens = special_tokens

    def extract_result(self, result: str) -> str | None:
        without_special_tokens = result
        for token in self.special_tokens:
            without_special_tokens = without_special_tokens.replace(token, "")
        if len(without_special_tokens) == len(result):
            return None
        return without_special_tokens
