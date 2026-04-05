# Task 040: Mark-Sweep Garbage Collector Tracing Bug

## Description

A mark-sweep garbage collector manages heap-allocated objects with reference tracking.
The mark phase starts from root objects and should recursively traverse all references
to mark reachable objects. The sweep phase then frees unmarked objects.

## Bug

The mark phase only marks the direct root objects but does not recursively follow
references stored in container fields (like list elements or object fields).
Objects reachable only through other objects (not direct roots) are incorrectly
swept as garbage.

## Expected Behavior

The mark phase should perform a full transitive closure: starting from roots,
recursively mark all objects reachable via reference chains of any depth.
