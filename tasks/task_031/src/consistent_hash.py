"""
Consistent hashing ring for distributed hash tables.

Supports virtual nodes, node addition/removal, and key-to-node mapping.
Uses bisect for efficient ring lookup.
"""

import hashlib
import bisect
from typing import Optional, List, Dict, Set, Tuple, Any


class ConsistentHashRing:
    """Consistent hash ring with virtual nodes for balanced distribution."""

    def __init__(self, num_virtual: int = 150, hash_func=None):
        self.num_virtual = num_virtual
        self._hash_func = hash_func or self._default_hash
        self._ring: Dict[int, str] = {}
        self._sorted_hashes: List[int] = []
        self._nodes: Set[str] = set()

    def _default_hash(self, key: str) -> int:
        h = hashlib.md5(key.encode('utf-8')).hexdigest()
        return int(h, 16)

    def add_node(self, node: str) -> List[int]:
        if node in self._nodes:
            return []

        self._nodes.add(node)
        added_hashes = []

        for i in range(self.num_virtual):
            virtual_key = f"{node}#vn{i}"
            h = self._hash_func(virtual_key)
            self._ring[h] = node
            bisect.insort(self._sorted_hashes, h)
            added_hashes.append(h)

        return added_hashes

    def remove_node(self, node: str) -> bool:
        if node not in self._nodes:
            return False

        self._nodes.discard(node)

        for i in range(self.num_virtual):
            virtual_key = f"{node}#vn{i}"
            h = self._hash_func(virtual_key)
            if h in self._ring:
                del self._ring[h]
                idx = bisect.bisect_left(self._sorted_hashes, h)
                if idx < len(self._sorted_hashes) and self._sorted_hashes[idx] == h:
                    self._sorted_hashes.pop(idx)

        return True

    def get_node(self, key: str) -> Optional[str]:
        if not self._sorted_hashes:
            return None

        h = self._hash_func(key)
        idx = bisect.bisect_right(self._sorted_hashes, h)

        if idx == len(self._sorted_hashes):
            idx = idx - 1

        ring_hash = self._sorted_hashes[idx]
        return self._ring[ring_hash]

    def get_nodes_for_key(self, key: str, count: int = 1) -> List[str]:
        if not self._sorted_hashes:
            return []

        h = self._hash_func(key)
        idx = bisect.bisect_right(self._sorted_hashes, h)

        result = []
        seen = set()
        ring_len = len(self._sorted_hashes)

        for offset in range(ring_len):
            pos = (idx + offset) % ring_len
            node = self._ring[self._sorted_hashes[pos]]
            if node not in seen:
                seen.add(node)
                result.append(node)
                if len(result) >= count:
                    break

        return result

    def get_all_nodes(self) -> Set[str]:
        return set(self._nodes)

    def get_ring_size(self) -> int:
        return len(self._sorted_hashes)

    def get_distribution(self, keys: List[str]) -> Dict[str, int]:
        distribution: Dict[str, int] = {node: 0 for node in self._nodes}
        for key in keys:
            node = self.get_node(key)
            if node:
                distribution[node] += 1
        return distribution

    def get_balance_score(self, keys: List[str]) -> float:
        if not self._nodes or not keys:
            return 0.0
        dist = self.get_distribution(keys)
        counts = list(dist.values())
        if not counts:
            return 0.0
        avg = sum(counts) / len(counts)
        if avg == 0:
            return 0.0
        variance = sum((c - avg) ** 2 for c in counts) / len(counts)
        return 1.0 - (variance ** 0.5) / avg


class WeightedConsistentHashRing(ConsistentHashRing):
    """Consistent hash ring where nodes can have different weights."""

    def __init__(self, base_virtual: int = 100, hash_func=None):
        super().__init__(num_virtual=base_virtual, hash_func=hash_func)
        self._base_virtual = base_virtual
        self._weights: Dict[str, float] = {}

    def add_node(self, node: str, weight: float = 1.0) -> List[int]:
        if node in self._nodes:
            return []

        self._weights[node] = weight
        actual_virtual = max(1, int(self._base_virtual * weight))
        self._nodes.add(node)
        added_hashes = []

        for i in range(actual_virtual):
            virtual_key = f"{node}#vn{i}"
            h = self._hash_func(virtual_key)
            self._ring[h] = node
            bisect.insort(self._sorted_hashes, h)
            added_hashes.append(h)

        return added_hashes

    def remove_node(self, node: str) -> bool:
        if node not in self._nodes:
            return False

        weight = self._weights.pop(node, 1.0)
        actual_virtual = max(1, int(self._base_virtual * weight))
        self._nodes.discard(node)

        for i in range(actual_virtual):
            virtual_key = f"{node}#vn{i}"
            h = self._hash_func(virtual_key)
            if h in self._ring:
                del self._ring[h]
                idx = bisect.bisect_left(self._sorted_hashes, h)
                if idx < len(self._sorted_hashes) and self._sorted_hashes[idx] == h:
                    self._sorted_hashes.pop(idx)

        return True

    def get_weight(self, node: str) -> float:
        return self._weights.get(node, 0.0)
