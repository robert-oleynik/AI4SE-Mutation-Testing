import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from .config import GeneratorConfig
from .generator import Mutation, MutationGenerator


def write_class_header(node: ts.Node) -> str:
    output = ""
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type == "decorator":
                output += child.text.decode() + "\n"
        node = node.child_by_field_name("definition")
    full_class = node.text
    body_node = node.child_by_field_name("body")
    offset = body_node.start_byte - node.start_byte
    output += full_class[:offset].decode()
    return output


class CommentRewriteGenerator(MutationGenerator):
    """
    Tries to regenerate new mutation by comment the old function and prompt the AI to
    regenerate this function.
    """

    def generate_prompt(self, node: ts.Node) -> str:
        context = Context(node)
        parent_class_node = context.get_parent_class()
        prompt = ""
        if parent_class_node is not None:
            class_with_decorator = Context(parent_class_node).with_decorater()
            prompt += write_class_header(class_with_decorator)

            indent = prompt.split(":")[-1][1:]
            prompt = prompt[: -len(indent)]

            body = parent_class_node.child_by_field_name("body")
            for child_node in body.children:
                if child_node.type == "decorated_definition":
                    child_node = child_node.child_by_field_name("definition")
                if child_node.type != "function_definition":
                    continue
                ctx = Context(child_node)
                if ctx.name() == context.name():
                    continue
                for decorator_node in ctx.decorators():
                    prompt += indent + decorator_node.text.decode() + "\n"
                prompt += indent + ctx.fn_signature() + "\n"
                n = child_node.child_by_field_name("body").child(0)
                if n.type == "expression_statement":
                    n = n.child(0)
                if n.type == "string":
                    prompt += indent + "    " + n.text.decode() + "\n"
                prompt += indent + "    ...\n\n"
        else:
            indent = ""

        for decorator_node in context.decorators():
            prompt += "#" + indent + decorator_node.text.decode() + "\n"
        fn_body = indent + node.text.decode()
        for line in fn_body.splitlines(True):
            prompt += "#" + line
        prompt += "\n\n"
        for decorator_node in context.decorators():
            prompt += indent + decorator_node.text.decode() + "\n"
        prompt += indent + context.fn_signature() + "\n"
        return prompt

    def generate(
        self, target: MutationTarget, config: GeneratorConfig
    ) -> list[Mutation]:
        import mutator.ai.llm

        prompt = self.generate_prompt(target.node)

        def transform(result: str) -> str:
            return result[len(prompt) :]

        results = mutator.ai.llm.prompt(
            prompt,
            transform_result=transform,
            **config.model_kwargs,
        )
        return Mutation.map(results)
