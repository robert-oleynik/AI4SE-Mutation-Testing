import tree_sitter as ts

from ..source import MutationTarget
from ..treesitter.context import Context
from ..treesitter.python import tsLang
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

_calls_query = tsLang.query(f"""
    (call function: [
        (identifier) @name
        (attribute attribute: (identifier) @name)
    ])
""")

class CommentRewriteGenerator(MutationGenerator):
    """
    Tries to regenerate new mutation by comment the old function and prompt the AI to
    regenerate this function.
    """

    def generate_prompt(self, node: ts.Node) -> str:
        method_context = Context(node)
        parent_class_node = method_context.get_parent_class()
        prompt = ""
        method_body = node.child_by_field_name("body").text.decode()
        method_name = method_context.name()
        function_calls = [node.text.decode() for _, match in _calls_query.matches(node) for _, node in match.items()]
        if parent_class_node is not None:
            class_with_decorator = Context(parent_class_node).with_decorater()
            prompt += write_class_header(class_with_decorator)

            indent = prompt.split(":")[-1][1:]
            prompt = prompt[: -len(indent)]

            class_body = parent_class_node.child_by_field_name("body")
            for sibling in class_body.children:
                if sibling.type == "decorated_definition":
                    sibling = sibling.child_by_field_name("definition")
                if sibling.type != "function_definition":
                    continue
                sibling_context = Context(sibling)
                sibling_name = sibling_context.name()

                if sibling_name == method_name:
                    continue
                if sibling_name == "__init__":
                    prompt += indent + sibling.text.decode() + "\n\n"
                    continue
                if sibling_name not in function_calls:
                    continue
                for decorator_node in sibling_context.decorators():
                    prompt += indent + decorator_node.text.decode() + "\n"
                prompt += indent + sibling_context.fn_signature() + "\n"
                candidate_docstring = sibling.child_by_field_name("body").child(0)
                if candidate_docstring.type == "expression_statement":
                    candidate_docstring = candidate_docstring.child(0)
                if candidate_docstring.type == "string":
                    prompt += indent + "    " + candidate_docstring.text.decode() + "\n"
                prompt += indent + "    ...\n\n"
        else:
            indent = ""

        for decorator_node in method_context.decorators():
            prompt += "#" + indent + decorator_node.text.decode() + "\n"
        fn_body = indent + node.text.decode()
        for line in fn_body.splitlines(True):
            prompt += "#" + line
        prompt += "\n\n"
        for decorator_node in method_context.decorators():
            prompt += indent + decorator_node.text.decode() + "\n"
        prompt += indent + method_context.fn_signature() + "\n"
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
