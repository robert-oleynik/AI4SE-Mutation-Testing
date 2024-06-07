import tree_sitter as ts

from ..treesitter.node import ts_node_parents


class Context:
    """
    Provides helper function to extract context of a given TreeSitter node.
    """

    def __init__(self, node: ts.Node):
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

    def fn_signature(self) -> ts.Node:
        assert self.node.type == "function_definition"
        return_type = self.node.child_by_field_name("return_type")
        return (
            "def "
            + self.node.child_by_field_name("name").text.decode()
            + self.node.child_by_field_name("parameters").text.decode()
            + (f" -> {return_type.text.decode()}" if return_type is not None else "")
            + ":"
        )
