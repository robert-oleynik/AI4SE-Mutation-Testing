import gc
import pathlib
import random
from collections.abc import Callable

import torch
import transformers

from .limiter.limiter import Limiter, OutputStoppingCriteria
from .limiter.special_tokens import SpecialTokensLimiter
from .transform import identity

MAX_TOKEN_COUNT = 2048


class LLM:
    def __init__(
        self,
        device: str,
        model_id: str,
        limiter_classes: list[type[Limiter]] = [],
        checkpoint: pathlib.Path | None = None,
        **generate_kwargs,
    ):
        self.device = torch.device(device)
        self.tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
        if checkpoint is not None:
            import peft

            self.model = peft.AutoPeftModelForCausalLM.from_pretrained(
                checkpoint, device_map=self.device, torch_dtype=torch.float16
            )
        else:
            self.model = transformers.AutoModelForCausalLM.from_pretrained(
                model_id, device_map=self.device, torch_dtype=torch.float16
            )
        self.limiter_classes = limiter_classes
        self.generate_kwargs = generate_kwargs

    def generate(
        self,
        inputs,
        prompt_len: int,
        transform_result: Callable[[str], str],
        **extra_args,
    ) -> list[str]:
        token_count = inputs["input_ids"].shape[1]
        if token_count >= MAX_TOKEN_COUNT:
            print(f"\nwarning: prompt too long ({token_count}), skip")
            return []

        bos_len = len(self.tokenizer.bos_token)

        def transform(result: str) -> str:
            return transform_result(result[bos_len:])

        limiters = [limiter_class() for limiter_class in self.limiter_classes]
        stop_tokens = [self.tokenizer.eos_token, "<|file_separator|>"]
        limiters.append(SpecialTokensLimiter(stop_tokens))
        kwargs = {
            **self.generate_kwargs,
            **extra_args,
            "stopping_criteria": transformers.StoppingCriteriaList(
                [
                    OutputStoppingCriteria(
                        limiter, self.tokenizer, transform, prompt_len
                    )
                    for limiter in limiters
                ]
                + self.generate_kwargs.get("stopping_criteria", [])
                + extra_args.get("stopping_criteria", [])
            ),
        }
        try:
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **kwargs)
        except torch.cuda.OutOfMemoryError:
            print("\nwarning: caught out of memory error, skip")
            return []

        def decode(output):
            return transform(self.tokenizer.decode(output))

        def decode_and_trim(output):
            result = decode(output)
            while any(limiter.is_too_long(result, prompt_len) for limiter in limiters):
                output = output[:-1]
                result = decode(output)
            return result

        return [decode_and_trim(output) for output in outputs]

    def prompt(
        self, prompt: str, transform_result: Callable[[str], str], **extra_args
    ) -> list[str]:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        results = self.generate(inputs, len(prompt), transform_result, **extra_args)
        gc.collect()
        return results

    def force_branch(
        self,
        prompt: str,
        transform_result: Callable[[str], str],
        keep_prefix_len: int,
        **extra_args,
    ) -> list[str]:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        num_tokens = inputs.input_ids.shape[1]
        prefix_len = len(self.tokenizer(prompt[:keep_prefix_len]).input_ids)
        index = random.randint(prefix_len + 1, num_tokens)
        for key in inputs.keys():
            inputs[key] = inputs[key][:, :index]
        results = self.generate(
            inputs.to(self.device),
            transform_result=transform_result,
            **extra_args,
        )
        gc.collect()
        return results


llm: LLM
