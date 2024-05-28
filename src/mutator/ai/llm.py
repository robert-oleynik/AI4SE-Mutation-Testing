import torch
import transformers
import random

from .limiter.limiter import Limiter, OutputStoppingCriteria


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

    def generate(self, inputs, strip_prefix_len: int, **extra_args) -> list[str]:
        prefix_length = len(self.tokenizer.bos_token) + strip_prefix_len

        limiters = [limiter_class() for limiter_class in self.limiter_classes]
        kwargs = {
            **self.generate_kwargs,
            **extra_args,
            "stopping_criteria": transformers.StoppingCriteriaList(
                [
                    OutputStoppingCriteria(limiter, self.tokenizer, prefix_length)
                    for limiter in limiters
                ]
                + self.generate_kwargs.get("stopping_criteria", [])
                + extra_args.get("stopping_criteria", [])
            ),
        }
        outputs = self.model.generate(**inputs, **kwargs)

        def decode(output):
            result = self.tokenizer.decode(output)[prefix_length:]
            if any(limiter.is_too_long(result) for limiter in limiters):
                result = decode(output[:-1])
            return result

        return [decode(output) for output in outputs]

    def prompt(self, prompt: str, prompt_is_part_of_result=False, **extra_args) -> list[str]:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        strip_prefix_len = 0 if prompt_is_part_of_result else len(prompt)
        return self.generate(inputs, strip_prefix_len, **extra_args)

    def force_branch(self, prompt: str, keep_prefix_len: int, **extra_args) -> list[str]:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        num_tokens = inputs.input_ids.shape[1]
        prefix_len = len(self.tokenizer(prompt[:keep_prefix_len]).input_ids)
        index = random.randint(prefix_len + 1, num_tokens)
        for key in inputs.keys():
            inputs[key] = inputs[key][:,:index]
        return self.generate(inputs.to(self.device), strip_prefix_len=0, **extra_args)
