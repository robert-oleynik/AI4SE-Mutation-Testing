from dataclasses import dataclass


@dataclass
class LLMResult:
    prompt: str
    output: str
    transformed: str
    final: str
