import abc
from collections.abc import Callable

import torch
from transformers import PreTrainedTokenizer, StoppingCriteria


class Limiter(abc.ABC):
    @abc.abstractmethod
    def is_too_long(self, result: str, prompt_len: int) -> bool:
        raise NotImplementedError


class OutputStoppingCriteria(StoppingCriteria):
    def __init__(
        self,
        limiter: Limiter,
        tokenizer: PreTrainedTokenizer,
        transform_result: Callable[[str], str],
        prompt_len: int,
    ):
        self.limiter = limiter
        self.tokenizer = tokenizer
        self.transform_result = transform_result
        self.prompt_len = prompt_len

    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs
    ) -> bool:
        input = self.tokenizer.decode(input_ids[0])
        input = self.transform_result(input)
        return self.limiter.is_too_long(input, self.prompt_len)
