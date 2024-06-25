import abc
from collections.abc import Callable

import torch
from transformers import PreTrainedTokenizer, StoppingCriteria


class Limiter(abc.ABC):
    @abc.abstractmethod
    def extract_result(self, result: str) -> str | None:
        raise NotImplementedError


class OutputStoppingCriteria(StoppingCriteria):
    def __init__(
        self,
        limiter: Limiter,
        tokenizer: PreTrainedTokenizer,
        transform_result: Callable[[str], str],
    ):
        self.limiter = limiter
        self.tokenizer = tokenizer
        self.transform_result = transform_result

    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs
    ) -> bool:
        input = self.tokenizer.decode(input_ids[0])
        input = self.transform_result(input)
        return self.limiter.extract_result(input) is not None
