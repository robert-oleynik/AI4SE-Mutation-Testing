import tree_sitter as ts


class TreeCursor:
    """
    Modified TreeSitter TreeCursor skipping all comments.
    """

    def __init__(self, cursor: ts.TreeCursor):
        self.cursor = cursor
        self.node = self.cursor.node

    def _skip_comments(self) -> bool:
        while True:
            self.node = self.cursor.node
            if self.cursor.node.type != "comment":
                if self.cursor.node.type != "expression_statement":
                    return True
                if self.cursor.node.child(0).type != "string":
                    return True
            if not self.cursor.goto_next_sibling():
                return False

    def goto_first_child(self) -> bool:
        if not self.cursor.goto_first_child():
            return False
        return self._skip_comments()

    def goto_next_sibling(self) -> bool:
        if not self.cursor.goto_next_sibling():
            return False
        return self._skip_comments()

    def goto_parent(self):
        self.cursor.goto_parent()
        self.node = self.cursor.node


class PairTreeCursor:
    """
    Walks two trees in parallel and checks for equality.
    """

    def __init__(self, a: "ts.Cursor", b: "ts.Cursor"):
        self.a = a
        self.b = b

    def goto_first_child(self) -> tuple[ts.Node | None, ts.Node | None]:
        a = self.a.node if self.a.goto_first_child() else None
        b = self.b.node if self.b.goto_first_child() else None
        return a, b

    def goto_next_sibling(self) -> tuple[ts.Node | None, ts.Node | None]:
        a = self.a.node if self.a.goto_next_sibling() else None
        b = self.b.node if self.b.goto_next_sibling() else None
        return a, b

    def goto_parent(self):
        self.a.goto_parent()
        self.b.goto_parent()
        return self.a.node, self.b.node


def compare(
    a: ts.TreeCursor, b: ts.TreeCursor
) -> tuple[bool, ts.Node | None, ts.Node | None]:
    atob = {}
    cursor = PairTreeCursor(TreeCursor(a), TreeCursor(b))

    def _rec_compare(depth: int = 0) -> tuple[bool, ts.Node | None, ts.Node | None]:
        a_node, b_node = cursor.goto_first_child()
        if a_node is None and b_node is None:
            a_node, b_node = cursor.a.node, cursor.b.node
            if a_node.type == "identifier":
                apn = a_node.parent
                appn = apn.parent
                isfuncident = (
                    apn.type == "attribute"
                    and apn.child_by_field_name("attribute").id == a_node.id
                    and appn.type == "call"
                )
                if isfuncident and a_node.text != b_node.text:
                    return False, a_node, b_node
                a_ident = a_node.text
                b_ident = b_node.text
                if a_ident in atob and atob[a_ident] != b_ident:
                    return False, a_node, b_node
                atob[a_ident] = b_ident
                return True, None, None
            return a_node.text == b_node.text, a_node, b_node
        while a_node is not None and b_node is not None:
            if a_node.type != b_node.type:
                return False, a_node, b_node
            equal, an, bn = _rec_compare(depth + 1)
            if not equal:
                return False, an, bn
            a_node, b_node = cursor.goto_next_sibling()
        cursor.goto_parent()
        return a_node is None and b_node is None, a_node, b_node

    return _rec_compare()
