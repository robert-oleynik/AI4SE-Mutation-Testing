import typing

import tree_sitter as ts


def upgrade_to_ty(node: ts.Node, ty: str) -> ts.Node | None:
    while node.parent is not None and node.type != ty:
        node = node.parent
    return node


def ts_node_parents(node: ts.Node) -> typing.Generator[ts.Node, None, None]:
    parent = node.parent
    while parent is not None:
        yield parent
        parent = parent.parent
