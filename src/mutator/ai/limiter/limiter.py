import abc
import torch
from transformers import StoppingCriteria, PreTrainedTokenizer


class Limiter(abc.ABC):
    @abc.abstractmethod
    def is_too_long(self, result: str) -> bool:
        raise NotImplementedError


class OutputStoppingCriteria(StoppingCriteria):
    def __init__(self, limiter: Limiter, tokenizer: PreTrainedTokenizer, prefix_length: int):
        self.limiter = limiter
        self.tokenizer = tokenizer
        self.prefix_length = prefix_length

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        input = self.tokenizer.decode(input_ids[0])
        return self.limiter.is_too_long(input[self.prefix_length:])
