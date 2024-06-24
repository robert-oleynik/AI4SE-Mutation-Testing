import abc
from typing import Callable


class Limiter(abc.ABC):
    @abc.abstractmethod
    def is_too_long(self, result: str) -> bool:
        raise NotImplementedError


class OutputStoppingCriteria(StoppingCriteria):
    def __init__(self, limiter: Limiter, tokenizer: "PreTrainedTokenizer", transform_result: Callable[[str], str]):
        self.limiter = limiter
        self.tokenizer = tokenizer
        self.transform_result = transform_result

    def __call__(self, input_ids: "torch.LongTensor", scores: "torch.FloatTensor", **kwargs) -> bool:
        input = self.tokenizer.decode(input_ids[0])
        input = self.transform_result(input)
        return self.limiter.is_too_long(input)
