import torch
import transformers


class LLM:
    def __init__(self, device: str, model_id: str, **model_kwargs):
        self.device = torch.device(device)
        self.tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(
                model_id, device_map=self.device, torch_dtype=torch.float16)
        self.model_kwargs = model_kwargs

    def prompt(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(**inputs, **self.model_kwargs)
        return self.tokenizer.decode(output[0])
