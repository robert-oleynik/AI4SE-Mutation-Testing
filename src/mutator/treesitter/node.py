import tree_sitter as ts


def upgrade_to_ty(node: ts.Node, ty: str) -> ts.Node | None:
    while node.parent is not None and node.type != ty:
        node = node.parent
    return node
