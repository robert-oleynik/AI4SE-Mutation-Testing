import random

import torch
import transformers

from .limiter.limiter import Limiter, OutputStoppingCriteria
from typing import Callable


class LLM:
    def __init__(
        self,
        device: str,
        model_id: str,
        limiter_classes: list[type[Limiter]] = [],
        **generate_kwargs,
    ):
        self.device = torch.device(device)
        self.tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            model_id, device_map=self.device, torch_dtype=torch.float16
        )
        self.limiter_classes = limiter_classes
        self.generate_kwargs = generate_kwargs

    def generate(self, inputs, transform_result: Callable[[str], str], **extra_args) -> list[str]:
        bos_len = len(self.tokenizer.bos_token)

        def transform(result: str) -> str:
            return transform_result(result[bos_len:])

        limiters = [limiter_class() for limiter_class in self.limiter_classes]
        kwargs = {
            **self.generate_kwargs,
            **extra_args,
            "stopping_criteria": transformers.StoppingCriteriaList(
                [
                    OutputStoppingCriteria(limiter, self.tokenizer, transform)
                    for limiter in limiters
                ]
                + self.generate_kwargs.get("stopping_criteria", [])
                + extra_args.get("stopping_criteria", [])
            ),
        }
        outputs = self.model.generate(**inputs, **kwargs)

        def decode(output):
            decoded = self.tokenizer.decode(output)
            if decoded.endswith(self.tokenizer.eos_token):
                return transform(decoded[:-len(self.tokenizer.eos_token)])
            result = transform(decoded)
            if any(limiter.is_too_long(result) for limiter in limiters):
                return transform(self.tokenizer.decode(output[:-1]))
            return result

        return [decode(output) for output in outputs]

    def prompt(
        self, prompt: str, transform_result: Callable[[str], str], **extra_args
    ) -> list[str]:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        return self.generate(inputs, transform_result, **extra_args)

    def force_branch(
        self, prompt: str, keep_prefix_len: int, **extra_args
    ) -> list[str]:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        num_tokens = inputs.input_ids.shape[1]
        prefix_len = len(self.tokenizer(prompt[:keep_prefix_len]).input_ids)
        index = random.randint(prefix_len + 1, num_tokens)
        for key in inputs.keys():
            inputs[key] = inputs[key][:, :index]
        return self.generate(inputs.to(self.device), strip_prefix_len=0, **extra_args)


def identity(result: str) -> str:
    return result


def trim_prompt(prompt: str) -> Callable[[str], str]:
    prompt_len = len(prompt)

    def transform(result: str) -> str:
        return result[prompt_len:]

    return transform
