import torch
import transformers
from typing import Type
from .limiter.limiter import Limiter


class LLM:
    def __init__(self, device: str, model_id: str, limiter_class: Type[Limiter], **model_kwargs):
        self.device = torch.device(device)
        self.tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(
                model_id, device_map=self.device, torch_dtype=torch.float16)
        self.limiter_class = limiter_class
        self.model_kwargs = model_kwargs

    def _next_token(self, inputs) -> int:
        logit = self.model(**inputs).logits[0][-1]
        token = torch.argmax(torch.softmax(logit, 0)).item()
        return self.tokenizer.decode([token])

    def prompt(self, prompt: str) -> str:
        limiter = self.limiter_class()
        result = ""
        while True:
            input = prompt + result
            inputs = self.tokenizer(input, return_tensors="pt").to(self.device)
            token = self._next_token(inputs)
            if token == self.tokenizer.eos_token or token == "<|file_separator|>":
                break
            if limiter.is_too_long(result + token):
                break
            result += token
        return result
