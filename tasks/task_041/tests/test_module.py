import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.buddy_allocator import BuddyAllocator


class TestBasicAllocation:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_single_alloc(self):
        ba = BuddyAllocator(max_order=4, min_order=0)  # 16 units
        addr = ba.alloc(1)
        assert addr is not None
        assert ba.get_allocated_memory() == 1

    @pytest.mark.pass_to_pass
    def test_alloc_full_block(self):
        ba = BuddyAllocator(max_order=4, min_order=0)
        addr = ba.alloc(16)
        assert addr is not None
        assert addr == 0
        assert ba.get_free_memory() == 0

    @pytest.mark.pass_to_pass
    def test_alloc_too_large(self):
        ba = BuddyAllocator(max_order=4, min_order=0)
        addr = ba.alloc(17)
        assert addr is None


class TestCoalescing:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_free_coalesces_buddies(self):
        """Freeing both buddies should coalesce into a larger block."""
        ba = BuddyAllocator(max_order=4, min_order=0)  # 16 units
        a1 = ba.alloc(8)  # order 3, addr 0
        a2 = ba.alloc(8)  # order 3, addr 8
        assert a1 is not None and a2 is not None
        assert ba.get_free_memory() == 0

        ba.free(a1)
        ba.free(a2)

        assert ba.get_free_memory() == 16
        errors = ba.verify_integrity()
        assert errors == [], f"Integrity errors: {errors}"
        assert len(ba.free_lists[4]) == 1, (
            f"Expected single order-4 block after coalescing, got free_lists={ba.free_lists}"
        )

    @pytest.mark.fail_to_pass
    def test_alloc_free_alloc_same_size(self):
        """After allocating and freeing, should be able to allocate the full pool again."""
        ba = BuddyAllocator(max_order=3, min_order=0)  # 8 units

        addrs = []
        for _ in range(8):
            addr = ba.alloc(1)
            assert addr is not None
            addrs.append(addr)

        for addr in addrs:
            ba.free(addr)

        errors = ba.verify_integrity()
        assert errors == [], f"Integrity errors after free: {errors}"

        big = ba.alloc(8)
        assert big is not None, "Should be able to allocate full pool after freeing all"

    @pytest.mark.fail_to_pass
    def test_interleaved_alloc_free_integrity(self):
        """Interleaved alloc/free should maintain memory integrity."""
        ba = BuddyAllocator(max_order=5, min_order=0)  # 32 units

        a = ba.alloc(4)   # order 2
        b = ba.alloc(4)   # order 2
        c = ba.alloc(8)   # order 3
        d = ba.alloc(2)   # order 1

        ba.free(a)
        ba.free(c)
        ba.free(b)

        errors = ba.verify_integrity()
        assert errors == [], f"Integrity errors: {errors}"

        big = ba.alloc(16)
        assert big is not None, "Should be able to alloc 16 after freeing 4+4+8 contiguously"

    @pytest.mark.fail_to_pass
    def test_buddy_address_correct(self):
        """Buddy of block at addr 0 order 2 should be addr 4, not addr 2."""
        ba = BuddyAllocator(max_order=4, min_order=0)  # 16 units

        # Allocate four order-1 (size 2) blocks: addrs 0, 2, 4, 6
        a = ba.alloc(2)  # order 1, addr 0
        b = ba.alloc(2)  # order 1, addr 2
        c = ba.alloc(2)  # order 1, addr 4
        d = ba.alloc(2)  # order 1, addr 6

        # Free block at addr 0 (order 1). Its buddy is at addr 0 XOR 2 = addr 2
        ba.free(a)

        # Free block at addr 2 (order 1). Its buddy is at addr 2 XOR 2 = addr 0
        # Both buddies free -> should coalesce into order 2 block at addr 0
        ba.free(b)

        # Now free block at addr 4 (order 1). Its buddy is at addr 4 XOR 2 = addr 6
        ba.free(c)

        # Free block at addr 6. Its buddy is addr 6 XOR 2 = addr 4. Coalesce to order 2.
        ba.free(d)

        # After coalescing all pairs, we should have two order-2 blocks at addrs 0 and 4
        # Those are true buddies (0 XOR 4 = 4) so they should coalesce into one order-3 block
        # Then that coalesces with the other order-3 block to get back to order-4

        errors = ba.verify_integrity()
        assert errors == [], f"Integrity errors: {errors}"

        # With correct buddy calc, everything should coalesce back to a single order-4 block
        assert ba.get_free_memory() == 16
        assert len(ba.free_lists[4]) == 1, (
            f"All 4 blocks should coalesce back to one order-4 block. "
            f"Free lists: {dict((k,v) for k,v in ba.free_lists.items() if v)}"
        )
