"""
Mark-sweep garbage collector simulation.

Manages a heap of objects with reference tracking. Supports primitive values,
container objects (lists, dictionaries), and composite objects with named fields.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union


class ObjType(Enum):
    INTEGER = auto()
    STRING = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    LIST = auto()
    DICT = auto()
    OBJECT = auto()
    NULL = auto()


@dataclass
class HeapObject:
    """An object on the managed heap."""
    obj_id: int
    obj_type: ObjType
    marked: bool = False
    value: Any = None
    references: List[int] = field(default_factory=list)
    fields: Dict[str, int] = field(default_factory=dict)
    size: int = 1

    def get_all_references(self) -> List[int]:
        """Return all object IDs this object references."""
        refs = list(self.references)
        refs.extend(self.fields.values())
        return refs


class Heap:
    """Managed heap for garbage-collected objects."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.objects: Dict[int, HeapObject] = {}
        self._next_id = 1
        self.total_allocated = 0
        self.total_freed = 0

    def _alloc_id(self) -> int:
        obj_id = self._next_id
        self._next_id += 1
        return obj_id

    def allocate_primitive(self, obj_type: ObjType, value: Any) -> int:
        if len(self.objects) >= self.max_size:
            raise MemoryError("Heap exhausted")
        obj_id = self._alloc_id()
        obj = HeapObject(obj_id=obj_id, obj_type=obj_type, value=value, size=1)
        self.objects[obj_id] = obj
        self.total_allocated += 1
        return obj_id

    def allocate_list(self, elements: Optional[List[int]] = None) -> int:
        if len(self.objects) >= self.max_size:
            raise MemoryError("Heap exhausted")
        obj_id = self._alloc_id()
        refs = list(elements) if elements else []
        obj = HeapObject(
            obj_id=obj_id, obj_type=ObjType.LIST,
            references=refs, size=1 + len(refs)
        )
        self.objects[obj_id] = obj
        self.total_allocated += 1
        return obj_id

    def allocate_dict(self, entries: Optional[Dict[str, int]] = None) -> int:
        if len(self.objects) >= self.max_size:
            raise MemoryError("Heap exhausted")
        obj_id = self._alloc_id()
        flds = dict(entries) if entries else {}
        obj = HeapObject(
            obj_id=obj_id, obj_type=ObjType.DICT,
            fields=flds, size=1 + len(flds)
        )
        self.objects[obj_id] = obj
        self.total_allocated += 1
        return obj_id

    def allocate_object(self, fields: Optional[Dict[str, int]] = None) -> int:
        if len(self.objects) >= self.max_size:
            raise MemoryError("Heap exhausted")
        obj_id = self._alloc_id()
        flds = dict(fields) if fields else {}
        obj = HeapObject(
            obj_id=obj_id, obj_type=ObjType.OBJECT,
            fields=flds, size=1 + len(flds)
        )
        self.objects[obj_id] = obj
        self.total_allocated += 1
        return obj_id

    def get(self, obj_id: int) -> HeapObject:
        if obj_id not in self.objects:
            raise ValueError(f"Object {obj_id} not found on heap (possibly freed)")
        return self.objects[obj_id]

    def set_field(self, obj_id: int, field_name: str, ref_id: int):
        obj = self.get(obj_id)
        obj.fields[field_name] = ref_id

    def append_ref(self, obj_id: int, ref_id: int):
        obj = self.get(obj_id)
        obj.references.append(ref_id)

    def remove_ref(self, obj_id: int, ref_id: int):
        obj = self.get(obj_id)
        if ref_id in obj.references:
            obj.references.remove(ref_id)

    def free(self, obj_id: int):
        if obj_id in self.objects:
            del self.objects[obj_id]
            self.total_freed += 1

    def object_count(self) -> int:
        return len(self.objects)


class GarbageCollector:
    """Mark-sweep garbage collector."""

    def __init__(self, heap: Heap):
        self.heap = heap
        self.roots: Set[int] = set()
        self.collections_run = 0
        self.total_objects_freed = 0

    def add_root(self, obj_id: int):
        self.roots.add(obj_id)

    def remove_root(self, obj_id: int):
        self.roots.discard(obj_id)

    def _clear_marks(self):
        for obj in self.heap.objects.values():
            obj.marked = False

    def _mark(self, obj_id: int):
        """Mark an object as reachable."""
        if obj_id not in self.heap.objects:
            return
        obj = self.heap.objects[obj_id]
        if obj.marked:
            return
        obj.marked = True

    def _mark_phase(self):
        """Mark all objects reachable from roots."""
        for root_id in self.roots:
            if root_id in self.heap.objects:
                self._mark(root_id)

    def _sweep_phase(self) -> int:
        """Free all unmarked objects. Returns number of objects freed."""
        to_free = []
        for obj_id, obj in self.heap.objects.items():
            if not obj.marked:
                to_free.append(obj_id)

        for obj_id in to_free:
            self.heap.free(obj_id)

        return len(to_free)

    def collect(self) -> int:
        """Run a full garbage collection cycle. Returns number freed."""
        self._clear_marks()
        self._mark_phase()
        freed = self._sweep_phase()
        self.collections_run += 1
        self.total_objects_freed += freed
        return freed

    def is_reachable(self, obj_id: int) -> bool:
        """Check if an object would survive collection."""
        self._clear_marks()
        self._mark_phase()
        if obj_id in self.heap.objects:
            return self.heap.objects[obj_id].marked
        return False


class ManagedRuntime:
    """High-level runtime using the garbage collector."""

    def __init__(self, heap_size: int = 10000, gc_threshold: int = 100):
        self.heap = Heap(max_size=heap_size)
        self.gc = GarbageCollector(self.heap)
        self.gc_threshold = gc_threshold
        self.variables: Dict[str, int] = {}
        self._alloc_since_gc = 0

    def _maybe_collect(self):
        self._alloc_since_gc += 1
        if self._alloc_since_gc >= self.gc_threshold:
            self.gc.collect()
            self._alloc_since_gc = 0

    def _update_roots(self):
        self.gc.roots = set(self.variables.values())

    def create_int(self, name: str, value: int) -> int:
        obj_id = self.heap.allocate_primitive(ObjType.INTEGER, value)
        self.variables[name] = obj_id
        self._update_roots()
        self._maybe_collect()
        return obj_id

    def create_string(self, name: str, value: str) -> int:
        obj_id = self.heap.allocate_primitive(ObjType.STRING, value)
        self.variables[name] = obj_id
        self._update_roots()
        self._maybe_collect()
        return obj_id

    def create_list(self, name: str, element_ids: Optional[List[int]] = None) -> int:
        obj_id = self.heap.allocate_list(element_ids)
        self.variables[name] = obj_id
        self._update_roots()
        self._maybe_collect()
        return obj_id

    def create_object(self, name: str, fields: Optional[Dict[str, int]] = None) -> int:
        obj_id = self.heap.allocate_object(fields)
        self.variables[name] = obj_id
        self._update_roots()
        self._maybe_collect()
        return obj_id

    def delete_variable(self, name: str):
        if name in self.variables:
            del self.variables[name]
            self._update_roots()

    def get_variable(self, name: str) -> Optional[HeapObject]:
        obj_id = self.variables.get(name)
        if obj_id and obj_id in self.heap.objects:
            return self.heap.get(obj_id)
        return None
