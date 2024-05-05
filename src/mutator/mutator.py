import torch
import logging
from transformers import GemmaTokenizer, AutoModelForCausalLM
from .project import Project, SourceFile, MutationTarget


class Mutator:
    def __init__(self, project: Project, *, model_id: str, **model_kwargs):
        self.project = project
        self.gpu = torch.device("cuda:0")
        self.tokenizer = GemmaTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, device_map=self.gpu, torch_dtype=torch.float16)
        self.model_kwargs = model_kwargs

    def query(self, prompt: str) -> str:
        logging.info("prompt:\n=============\n%s\n=============", prompt)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.gpu)
        output = self.model.generate(**inputs, **self.model_kwargs)
        answer = self.tokenizer.decode(output[0])
        return (answer
                .strip()
                .removeprefix("<bos>")
                .removesuffix("<eos>")
                .strip()
                .removesuffix("<|file_separator|>")
                .strip())

    def mutate(self, source: SourceFile, target: MutationTarget) -> str:
        prompt = "# Original version\n"
        prompt += target.content(source.content).decode()
        prompt += "\n\n# Mutated version for mutation testing\n"
        answer = self.query(prompt)
        return answer[len(prompt):]
