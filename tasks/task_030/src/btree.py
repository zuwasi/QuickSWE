"""
B-tree implementation supporting insert, search, delete, and in-order traversal.
Configurable minimum degree (t). Each node has at most 2t-1 keys.
"""

from typing import Optional, List, Tuple, Any


class BTreeNode:
    """A node in the B-tree."""

    def __init__(self, leaf: bool = True):
        self.keys: List[int] = []
        self.children: List["BTreeNode"] = []
        self.leaf: bool = leaf

    @property
    def n(self) -> int:
        return len(self.keys)

    def __repr__(self):
        return f"BTreeNode(keys={self.keys}, leaf={self.leaf})"


class BTree:
    """B-tree with configurable minimum degree t."""

    def __init__(self, t: int = 2):
        if t < 2:
            raise ValueError("Minimum degree must be at least 2")
        self.t = t
        self.root = BTreeNode(leaf=True)

    def search(self, key: int, node: Optional[BTreeNode] = None) -> Optional[Tuple[BTreeNode, int]]:
        if node is None:
            node = self.root

        i = 0
        while i < node.n and key > node.keys[i]:
            i += 1

        if i < node.n and key == node.keys[i]:
            return (node, i)

        if node.leaf:
            return None

        return self.search(key, node.children[i])

    def insert(self, key: int):
        root = self.root

        if root.n == 2 * self.t - 1:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
            self._insert_nonfull(new_root, key)
        else:
            self._insert_nonfull(root, key)

    def _insert_nonfull(self, node: BTreeNode, key: int):
        i = node.n - 1

        if node.leaf:
            node.keys.append(0)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1

            if node.children[i].n == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1

            self._insert_nonfull(node.children[i], key)

    def _split_child(self, parent: BTreeNode, index: int):
        t = self.t
        child = parent.children[index]
        mid = t - 1

        new_node = BTreeNode(leaf=child.leaf)
        median_key = child.keys[mid]

        new_node.keys = child.keys[mid:]
        child.keys = child.keys[:mid]

        if not child.leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]

        parent.children.insert(index + 1, new_node)
        parent.keys.insert(index, median_key)

    def inorder(self) -> List[int]:
        result = []
        self._inorder_walk(self.root, result)
        return result

    def _inorder_walk(self, node: BTreeNode, result: List[int]):
        for i in range(node.n):
            if not node.leaf:
                self._inorder_walk(node.children[i], result)
            result.append(node.keys[i])
        if not node.leaf:
            self._inorder_walk(node.children[node.n], result)

    def contains(self, key: int) -> bool:
        return self.search(key) is not None

    def minimum(self) -> Optional[int]:
        node = self.root
        if node.n == 0:
            return None
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def maximum(self) -> Optional[int]:
        node = self.root
        if node.n == 0:
            return None
        while not node.leaf:
            node = node.children[node.n]
        return node.keys[node.n - 1]

    def count_keys(self) -> int:
        return self._count_keys_rec(self.root)

    def _count_keys_rec(self, node: BTreeNode) -> int:
        total = node.n
        if not node.leaf:
            for child in node.children:
                total += self._count_keys_rec(child)
        return total

    def height(self) -> int:
        h = 0
        node = self.root
        while not node.leaf:
            h += 1
            node = node.children[0]
        return h

    def is_valid(self) -> bool:
        if self.root.n == 0:
            return True
        return self._validate(self.root, None, None, self.root is self.root)

    def _validate(self, node: BTreeNode, min_key: Optional[int],
                  max_key: Optional[int], is_root: bool) -> bool:
        if not is_root:
            if node.n < self.t - 1:
                return False
        if node.n > 2 * self.t - 1:
            return False

        for i in range(node.n - 1):
            if node.keys[i] >= node.keys[i + 1]:
                return False

        if min_key is not None and node.keys[0] <= min_key:
            return False
        if max_key is not None and node.keys[-1] >= max_key:
            return False

        if not node.leaf:
            if len(node.children) != node.n + 1:
                return False
            for i, child in enumerate(node.children):
                child_min = node.keys[i - 1] if i > 0 else min_key
                child_max = node.keys[i] if i < node.n else max_key
                if not self._validate(child, child_min, child_max, False):
                    return False

        return True

    def level_order(self) -> List[List[List[int]]]:
        if self.root.n == 0:
            return []
        levels = []
        queue = [self.root]
        while queue:
            level_keys = []
            next_queue = []
            for node in queue:
                level_keys.append(list(node.keys))
                if not node.leaf:
                    next_queue.extend(node.children)
            levels.append(level_keys)
            queue = next_queue
        return levels
