"""
Red-Black Tree implementation with insert and delete operations.
Supports integer keys with standard RB-tree balancing.
"""

RED = "RED"
BLACK = "BLACK"


class RBNode:
    """A node in the red-black tree."""

    def __init__(self, key, color=RED):
        self.key = key
        self.color = color
        self.left = None
        self.right = None
        self.parent = None

    def __repr__(self):
        return f"RBNode({self.key}, {self.color})"


class RBTree:
    """Red-Black Tree supporting insert and delete with full rebalancing."""

    def __init__(self):
        self.NIL = RBNode(key=None, color=BLACK)
        self.NIL.left = self.NIL
        self.NIL.right = self.NIL
        self.NIL.parent = self.NIL
        self.root = self.NIL

    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        if y.left is not self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is self.NIL:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _right_rotate(self, y):
        x = y.left
        y.left = x.right
        if x.right is not self.NIL:
            x.right.parent = y
        x.parent = y.parent
        if y.parent is self.NIL:
            self.root = x
        elif y is y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x

    def insert(self, key):
        node = RBNode(key)
        node.left = self.NIL
        node.right = self.NIL
        node.parent = self.NIL

        parent = self.NIL
        current = self.root

        while current is not self.NIL:
            parent = current
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                return

        node.parent = parent
        if parent is self.NIL:
            self.root = node
        elif key < parent.key:
            parent.left = node
        else:
            parent.right = node

        node.color = RED
        self._insert_fixup(node)

    def _insert_fixup(self, z):
        while z.parent.color == RED:
            if z.parent is z.parent.parent.left:
                uncle = z.parent.parent.right
                if uncle.color == RED:
                    z.parent.color = BLACK
                    uncle.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
            else:
                uncle = z.parent.parent.left
                if uncle.color == RED:
                    z.parent.color = BLACK
                    uncle.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)
        self.root.color = BLACK

    def _transplant(self, u, v):
        if u.parent is self.NIL:
            self.root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _tree_minimum(self, node):
        while node.left is not self.NIL:
            node = node.left
        return node

    def search(self, key):
        current = self.root
        while current is not self.NIL:
            if key == current.key:
                return current
            elif key < current.key:
                current = current.left
            else:
                current = current.right
        return None

    def delete(self, key):
        z = self.search(key)
        if z is None:
            return False

        y = z
        y_original_color = y.color

        if z.left is self.NIL:
            x = z.right
            self._transplant(z, z.right)
        elif z.right is self.NIL:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._tree_minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent is z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        if y_original_color == BLACK:
            self._delete_fixup(x)
        return True

    def _delete_fixup(self, x):
        while x is not self.root and x.color == BLACK:
            if x is x.parent.left:
                sibling = x.parent.right
                if sibling.color == RED:
                    sibling.color = BLACK
                    x.parent.color = RED
                    self._left_rotate(x.parent)
                    sibling = x.parent.right
                if sibling.left.color == BLACK and sibling.right.color == BLACK:
                    sibling.color = RED
                    x = x.parent.left
                else:
                    if sibling.right.color == BLACK:
                        sibling.left.color = BLACK
                        sibling.color = RED
                        self._right_rotate(sibling)
                        sibling = x.parent.right
                    sibling.color = x.parent.color
                    x.parent.color = BLACK
                    sibling.right.color = BLACK
                    self._left_rotate(x.parent)
                    x = self.root
            else:
                sibling = x.parent.left
                if sibling.color == RED:
                    sibling.color = BLACK
                    x.parent.color = RED
                    self._right_rotate(x.parent)
                    sibling = x.parent.left
                if sibling.right.color == BLACK and sibling.left.color == BLACK:
                    sibling.color = RED
                    x = x.parent.right
                else:
                    if sibling.left.color == BLACK:
                        sibling.right.color = BLACK
                        sibling.color = RED
                        self._left_rotate(sibling)
                        sibling = x.parent.left
                    sibling.color = x.parent.color
                    x.parent.color = BLACK
                    sibling.left.color = BLACK
                    self._right_rotate(x.parent)
                    x = self.root
        x.color = BLACK

    def inorder(self):
        result = []
        self._inorder_walk(self.root, result)
        return result

    def _inorder_walk(self, node, result):
        if node is not self.NIL:
            self._inorder_walk(node.left, result)
            result.append(node.key)
            self._inorder_walk(node.right, result)

    def black_height(self, node=None):
        if node is None:
            node = self.root
        if node is self.NIL:
            return 1
        left_bh = self.black_height(node.left)
        right_bh = self.black_height(node.right)
        if left_bh != right_bh:
            return -1
        return left_bh + (1 if node.color == BLACK else 0)

    def is_valid_rb_tree(self):
        if self.root is self.NIL:
            return True
        if self.root.color != BLACK:
            return False
        if self.black_height() == -1:
            return False
        return self._check_no_consecutive_reds(self.root)

    def _check_no_consecutive_reds(self, node):
        if node is self.NIL:
            return True
        if node.color == RED:
            if node.left.color == RED or node.right.color == RED:
                return False
        return (self._check_no_consecutive_reds(node.left) and
                self._check_no_consecutive_reds(node.right))

    def size(self):
        return self._count(self.root)

    def _count(self, node):
        if node is self.NIL:
            return 0
        return 1 + self._count(node.left) + self._count(node.right)
