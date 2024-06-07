import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
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
        decorated_node = context.with_decorater()
        parent_class_node = context.get_parent_class()
        prompt = ""
        if parent_class_node is not None:
            class_with_decorator = Context(parent_class_node).with_decorater()
            prompt += write_class_header(class_with_decorator)
        indent = prompt.split(":")[-1][1:]
        prompt = prompt[: -len(indent)]
        if decorated_node.type == "decorated_definition":
            for child in decorated_node.children:
                if child.type == "decorator":
                    prompt += "#" + indent + child.text.decode() + "\n"
        fn_body = indent + node.text.decode()
        for line in fn_body.splitlines(True):
            prompt += "#" + line
        prompt += "\n\n" + indent + context.fn_signature() + "\n"
        return prompt

    def generate(self, target: MutationTarget) -> list[Mutation]:
        raise NotImplementedError
