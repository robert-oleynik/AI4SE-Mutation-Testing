import torch
import transformers

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

    def prompt(self, prompt: str, prompt_is_part_of_result=False, **extra_args) -> str:
        prefix_length = len(self.tokenizer.bos_token)
        if not prompt_is_part_of_result:
            prefix_length += len(prompt)

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
            ),
        }
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, **kwargs)[0]

        def decode(output):
            result = self.tokenizer.decode(output)[prefix_length:]
            if any(limiter.is_too_long(result) for limiter in limiters):
                result = decode(output[:-1])
            return result

        return [decode(output) for output in outputs]
