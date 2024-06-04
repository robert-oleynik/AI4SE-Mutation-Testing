from ..source import MutationTarget
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


class ForcedBranchGenerator(MutationGenerator):
    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai

        prompt = target.content().decode()
        signature = target.get_signature().decode()
        results = mutator.ai.llm.force_branch(
            prompt, keep_prefix_len=len(signature), **config.model_kwargs
        )
        return Mutation.map(results)
