"""
Buddy memory allocator.

Manages a power-of-two-sized memory pool using the buddy system.
Supports allocation and deallocation with automatic splitting and coalescing.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import math


@dataclass
class Block:
    """A memory block in the buddy allocator."""
    address: int
    order: int  # block size = 2^order
    is_free: bool = True

    @property
    def size(self) -> int:
        return 1 << self.order


class BuddyAllocator:
    """
    Buddy memory allocator.
    
    Manages a memory pool of size 2^max_order units.
    Minimum allocation size is 2^min_order units.
    """

    def __init__(self, max_order: int = 10, min_order: int = 0):
        if min_order > max_order:
            raise ValueError("min_order cannot exceed max_order")

        self.max_order = max_order
        self.min_order = min_order
        self.total_size = 1 << max_order

        self.free_lists: Dict[int, List[int]] = {}
        for order in range(min_order, max_order + 1):
            self.free_lists[order] = []

        self.free_lists[max_order].append(0)

        self.allocated: Dict[int, int] = {}

        self.block_info: Dict[int, Block] = {}
        self.block_info[0] = Block(address=0, order=max_order, is_free=True)

        self._stats_allocs = 0
        self._stats_frees = 0
        self._stats_splits = 0
        self._stats_merges = 0

    def _order_for_size(self, size: int) -> int:
        """Find the minimum order that fits the requested size."""
        if size <= 0:
            raise ValueError("Size must be positive")
        order = max(self.min_order, math.ceil(math.log2(max(size, 1))))
        if order > self.max_order:
            raise MemoryError(f"Requested size {size} exceeds maximum block size")
        return order

    def _split_block(self, address: int, current_order: int, target_order: int):
        """Split a block down to the target order."""
        while current_order > target_order:
            current_order -= 1
            buddy_addr = address + (1 << current_order)

            self.block_info[address] = Block(
                address=address, order=current_order, is_free=True
            )
            self.block_info[buddy_addr] = Block(
                address=buddy_addr, order=current_order, is_free=True
            )

            self.free_lists[current_order].append(buddy_addr)
            self._stats_splits += 1

    def _find_buddy_address(self, address: int, order: int) -> int:
        """Calculate the buddy address for a block."""
        return address ^ (1 << (order - 1))

    def alloc(self, size: int) -> Optional[int]:
        """
        Allocate a block of at least `size` units.
        Returns the block address, or None if allocation fails.
        """
        try:
            order = self._order_for_size(size)
        except (ValueError, MemoryError):
            return None

        for current_order in range(order, self.max_order + 1):
            if self.free_lists[current_order]:
                address = self.free_lists[current_order].pop(0)

                if current_order > order:
                    self._split_block(address, current_order, order)

                self.block_info[address] = Block(
                    address=address, order=order, is_free=False
                )
                self.allocated[address] = order
                self._stats_allocs += 1
                return address

        return None

    def free(self, address: int):
        """Free a previously allocated block."""
        if address not in self.allocated:
            raise ValueError(f"Address {address} was not allocated")

        order = self.allocated.pop(address)
        self.block_info[address] = Block(
            address=address, order=order, is_free=True
        )

        self._coalesce(address, order)
        self._stats_frees += 1

    def _coalesce(self, address: int, order: int):
        """Try to merge the block with its buddy, recursively."""
        while order < self.max_order:
            buddy_addr = self._find_buddy_address(address, order)

            if buddy_addr not in self.block_info:
                break
            buddy = self.block_info[buddy_addr]
            if not buddy.is_free or buddy.order != order:
                break

            if buddy_addr in self.free_lists[order]:
                self.free_lists[order].remove(buddy_addr)
            else:
                break

            del self.block_info[buddy_addr]

            merged_addr = min(address, buddy_addr)
            order += 1
            address = merged_addr

            self.block_info[address] = Block(
                address=address, order=order, is_free=True
            )
            self._stats_merges += 1

        self.free_lists[order].append(address)

    def get_free_memory(self) -> int:
        """Return total free memory."""
        total = 0
        for order, addrs in self.free_lists.items():
            total += len(addrs) * (1 << order)
        return total

    def get_allocated_memory(self) -> int:
        """Return total allocated memory."""
        total = 0
        for addr, order in self.allocated.items():
            total += 1 << order
        return total

    def get_fragmentation(self) -> float:
        """Return fragmentation ratio (0 = no fragmentation)."""
        free = self.get_free_memory()
        if free == 0:
            return 0.0
        largest_free = 0
        for order in range(self.max_order, self.min_order - 1, -1):
            if self.free_lists.get(order):
                largest_free = 1 << order
                break
        if largest_free == 0:
            return 1.0
        return 1.0 - (largest_free / free)

    def dump_state(self) -> str:
        """Return a string representation of allocator state."""
        lines = [f"BuddyAllocator (total={self.total_size})"]
        lines.append(f"  Allocated: {self.get_allocated_memory()}")
        lines.append(f"  Free: {self.get_free_memory()}")
        lines.append(f"  Stats: allocs={self._stats_allocs} frees={self._stats_frees} "
                      f"splits={self._stats_splits} merges={self._stats_merges}")
        lines.append("  Free lists:")
        for order in range(self.min_order, self.max_order + 1):
            addrs = self.free_lists[order]
            if addrs:
                lines.append(f"    order {order} (size {1 << order}): {sorted(addrs)}")
        lines.append("  Allocated blocks:")
        for addr in sorted(self.allocated.keys()):
            order = self.allocated[addr]
            lines.append(f"    addr={addr} order={order} size={1 << order}")
        return "\n".join(lines)

    def verify_integrity(self) -> List[str]:
        """Verify allocator invariants. Returns list of errors found."""
        errors = []

        total = self.get_free_memory() + self.get_allocated_memory()
        if total != self.total_size:
            errors.append(f"Total memory mismatch: {total} != {self.total_size}")

        all_regions = []
        for addr, order in self.allocated.items():
            all_regions.append((addr, 1 << order, "alloc"))
        for order, addrs in self.free_lists.items():
            for addr in addrs:
                all_regions.append((addr, 1 << order, "free"))

        all_regions.sort()
        for i in range(len(all_regions) - 1):
            addr1, size1, _ = all_regions[i]
            addr2, _, _ = all_regions[i + 1]
            if addr1 + size1 > addr2:
                errors.append(f"Overlapping regions at {addr1}+{size1} and {addr2}")

        return errors
