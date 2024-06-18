from dataclasses import dataclass


@dataclass
class GeneratorConfig:
    model_kwargs: dict
    tries_per_target: int
