import typing

import tree_sitter as ts

from ..treesitter.node import ts_node_parents
from ..treesitter.python import tsLang


_calls_query = tsLang.query(f"""
    (call function: [
        (identifier) @name
        (attribute attribute: (identifier) @name)
    ])
""")


class Context:
    """
    Provides helper function to extract context of a given TreeSitter node.
    """

    def __init__(self, node: ts.Node):
        if node.type == "decorated_definition":
            node = node.child_by_field_name("definition")
        self.node = node

    def get_parent_class(self) -> ts.Node | None:
        """
        Returns parent the parent class of this node. Will return None if this node is
        not nested inside a class.
        """
        for node in ts_node_parents(self.node):
            if node.type == "class_definition":
                return node
        return None

    def name(self) -> str:
        name_node = self.node.child_by_field_name("name")
        assert name_node.type == "identifier"
        return name_node.text.decode("utf-8")

    def with_decorater(self) -> ts.Node:
        """
        Returns the largest decorated directly adjacent to this node.
        """
        last = self.node
        for node in ts_node_parents(last):
            if node.type != "decorated_definition":
                return last
            last = node
        return last

    def decorators(self) -> typing.Generator[ts.Node, None, None]:
        decorated_node = self.with_decorater()
        if self.node == decorated_node:
            return
        for child in decorated_node.children:
            if child.type == "decorator":
                yield child

    def fn_signature(self) -> str:
        assert self.node.type == "function_definition"
        return_type = self.node.child_by_field_name("return_type")

        return (
            "def "
            + self.node.child_by_field_name("name").text.decode()
            + self.node.child_by_field_name("parameters").text.decode()
            + (f" -> {return_type.text.decode()}" if return_type is not None else "")
            + ":"
        )

    def docstring(self) -> ts.Node | None:
        candidate = self.node.child_by_field_name("body").child(0)
        if candidate.type == "expression_statement":
            candidate = candidate.child(0)
        return candidate if candidate.type == "string" else None

    @staticmethod
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

    def relevant_class_definition(self) -> str:
        parent_class_node = self.get_parent_class()
        if parent_class_node is None:
            return "", ""

        class_with_decorator = Context(parent_class_node).with_decorater()
        prompt = self.write_class_header(class_with_decorator)

        indent = prompt.split(":")[-1][1:]
        prompt = prompt[: -len(indent)]

        method_body = self.node.child_by_field_name("body").text.decode()
        method_name = self.name()

        function_calls = [node.text.decode() for _, match in _calls_query.matches(self.node) for _, node in match.items()]
        class_body = parent_class_node.child_by_field_name("body")
        for sibling in class_body.children:
            sibling_context = Context(sibling)
            if sibling_context.node.type != "function_definition":
                continue
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
            docstring = sibling_context.docstring()
            if docstring:
                prompt += indent + "    " + docstring.text.decode() + "\n"
            prompt += indent + "    ...\n\n"
        return prompt, indent
