from .limiter import Limiter


class SpecialTokensLimiter(Limiter):
    def __init__(self, special_tokens: list[str]) -> None:
        self.special_tokens = special_tokens

    def is_too_long(self, result: str) -> bool:
        return any(token in result for token in self.special_tokens)
