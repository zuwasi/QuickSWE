import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.gc import Heap, GarbageCollector, ObjType, ManagedRuntime


class TestBasicGC:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_direct_root_survives(self):
        heap = Heap()
        gc = GarbageCollector(heap)
        obj_id = heap.allocate_primitive(ObjType.INTEGER, 42)
        gc.add_root(obj_id)
        freed = gc.collect()
        assert freed == 0
        assert obj_id in heap.objects

    @pytest.mark.pass_to_pass
    def test_unreachable_is_freed(self):
        heap = Heap()
        gc = GarbageCollector(heap)
        obj_id = heap.allocate_primitive(ObjType.INTEGER, 42)
        freed = gc.collect()
        assert freed == 1
        assert obj_id not in heap.objects

    @pytest.mark.pass_to_pass
    def test_remove_root_then_collect(self):
        heap = Heap()
        gc = GarbageCollector(heap)
        obj_id = heap.allocate_primitive(ObjType.STRING, "hello")
        gc.add_root(obj_id)
        gc.collect()
        assert obj_id in heap.objects
        gc.remove_root(obj_id)
        gc.collect()
        assert obj_id not in heap.objects


class TestContainerTracing:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_list_elements_survive(self):
        """Objects referenced by a root list should survive collection."""
        heap = Heap()
        gc = GarbageCollector(heap)

        elem1 = heap.allocate_primitive(ObjType.INTEGER, 1)
        elem2 = heap.allocate_primitive(ObjType.INTEGER, 2)
        elem3 = heap.allocate_primitive(ObjType.INTEGER, 3)
        list_id = heap.allocate_list([elem1, elem2, elem3])

        gc.add_root(list_id)
        gc.collect()

        assert list_id in heap.objects, "Root list was freed"
        assert elem1 in heap.objects, "List element 1 was incorrectly freed"
        assert elem2 in heap.objects, "List element 2 was incorrectly freed"
        assert elem3 in heap.objects, "List element 3 was incorrectly freed"

    @pytest.mark.fail_to_pass
    def test_nested_object_fields_survive(self):
        """Objects referenced by fields of a root object should survive."""
        heap = Heap()
        gc = GarbageCollector(heap)

        name = heap.allocate_primitive(ObjType.STRING, "Alice")
        age = heap.allocate_primitive(ObjType.INTEGER, 30)
        person = heap.allocate_object({"name": name, "age": age})

        gc.add_root(person)
        gc.collect()

        assert person in heap.objects
        assert name in heap.objects, "Object field 'name' was incorrectly freed"
        assert age in heap.objects, "Object field 'age' was incorrectly freed"

    @pytest.mark.fail_to_pass
    def test_deep_reference_chain(self):
        """Objects at the end of a reference chain should survive."""
        heap = Heap()
        gc = GarbageCollector(heap)

        deep_val = heap.allocate_primitive(ObjType.INTEGER, 999)
        inner_list = heap.allocate_list([deep_val])
        middle = heap.allocate_object({"items": inner_list})
        outer = heap.allocate_object({"child": middle})

        gc.add_root(outer)
        gc.collect()

        assert outer in heap.objects
        assert middle in heap.objects, "Middle object was freed"
        assert inner_list in heap.objects, "Inner list was freed"
        assert deep_val in heap.objects, "Deep value was freed"

    @pytest.mark.fail_to_pass
    def test_cyclic_references_survive(self):
        """Cyclic references reachable from root should all survive."""
        heap = Heap()
        gc = GarbageCollector(heap)

        a = heap.allocate_object()
        b = heap.allocate_object()
        heap.set_field(a, "next", b)
        heap.set_field(b, "next", a)

        gc.add_root(a)
        gc.collect()

        assert a in heap.objects, "Node A was freed"
        assert b in heap.objects, "Node B (referenced by A) was freed"
