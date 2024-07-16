import gc
import pathlib
import random
from collections.abc import Callable

import torch
import transformers

from .limiter.limiter import Limiter, OutputStoppingCriteria
from .limiter.special_tokens import SpecialTokensLimiter
from .llm_result import LLMResult
from .llm_stats import LLMStats

MAX_TOKEN_COUNT = 2048


class LLM:
    def __init__(
        self,
        device: str,
        model_id_or_checkpoint: str | pathlib.Path,
        limiter_classes: list[type[Limiter]] | None = None,
        **generate_kwargs,
    ):
        self.stats = LLMStats()
        self.device = torch.device(device)
        if isinstance(model_id_or_checkpoint, pathlib.Path):
            import peft

            self.model = peft.AutoPeftModelForCausalLM.from_pretrained(
                model_id_or_checkpoint,
                device_map=self.device,
                torch_dtype=torch.float16,
            )
            model_id = self.model.peft_config["default"].base_model_name_or_path
        else:
            self.model = transformers.AutoModelForCausalLM.from_pretrained(
                model_id_or_checkpoint,
                device_map=self.device,
                torch_dtype=torch.float16,
            )
            model_id = model_id_or_checkpoint
        self.tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
        self.limiter_classes = limiter_classes or []
        self.generate_kwargs = generate_kwargs

    def reset_stats(self):
        self.stats = LLMStats()

    def generate(
        self,
        prompt: str,
        inputs: dict,
        transform_result: Callable[[str], str],
        **extra_args,
    ) -> list[LLMResult]:
        input_token_count = inputs["input_ids"].shape[1]
        if input_token_count >= MAX_TOKEN_COUNT:
            print(f"\nwarning: prompt too long ({input_token_count}), skip")
            self.stats.input_too_long_count += 1
            return []
        self.stats.generate_count += 1

        bos_len = len(self.tokenizer.bos_token)

        def transform(result: str) -> str:
            return transform_result(result[bos_len:])

        limiters = [limiter_class() for limiter_class in self.limiter_classes]
        eos_tokens = [
            self.tokenizer.eos_token,
            "<unk>",
            "<pad>",
            "<|fim_prefix|>",
            "<|fim_suffix|>",
            "<|fim_middle|>",
            "<|file_separator|>",
        ]
        eos_tokens = list(set(eos_tokens))
        eos_token_ids = self.tokenizer.convert_tokens_to_ids(eos_tokens) + [
            self.tokenizer.eos_token_id
        ]
        limiters.append(SpecialTokensLimiter(eos_tokens))
        kwargs = {
            **self.generate_kwargs,
            **extra_args,
            "eos_token_id": eos_token_ids,
            "stopping_criteria": transformers.StoppingCriteriaList(
                [
                    OutputStoppingCriteria(limiter, self.tokenizer, transform)
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
            self.stats.out_of_memory_count += 1
            return []

        def decode(output):
            output = self.tokenizer.decode(output)
            transformed = transform(output)
            result = transformed
            local_limiters = limiters.copy()
            while True:
                for limiter in local_limiters:
                    trimmed = limiter.extract_result(result)
                    if trimmed is not None:
                        result = trimmed
                        local_limiters.remove(limiter)
                        break
                else:
                    # no limiter trimmed anything
                    break
            return LLMResult(prompt, output, transformed, result)

        for output in outputs:
            self.stats.input_token_count += input_token_count
            null_token_indices = torch.where(output == 0)[0]
            output_token_count = (
                len(output)
                if len(null_token_indices) == 0
                else null_token_indices[0].item()
            )
            self.stats.output_token_count += output_token_count
        return [decode(output) for output in outputs]

    def prompt(
        self, prompt: str, transform_result: Callable[[str], str], **extra_args
    ) -> list[LLMResult]:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        results = self.generate(prompt, inputs, transform_result, **extra_args)
        gc.collect()
        return results

    def prompt_with_random_prefix(
        self,
        prompt: str,
        transform_result: Callable[[str], str],
        keep_prefix_len: int,
        **extra_args,
    ) -> list[LLMResult]:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        num_tokens = inputs.input_ids.shape[1]
        prefix_len = len(self.tokenizer(prompt[:keep_prefix_len]).input_ids)
        index = random.randint(prefix_len + 1, num_tokens)
        for key in inputs.keys():
            inputs[key] = inputs[key][:, :index]
        results = self.generate(
            prompt,
            inputs.to(self.device),
            transform_result=transform_result,
            **extra_args,
        )
        gc.collect()
        return results


llm: LLM
