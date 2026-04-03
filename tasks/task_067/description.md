# Bug: Virtual Dispatch with Object Slicing

## Description

An inheritance hierarchy: `Shape` (base) -> `Circle`, `Rectangle`. A `ShapeFactory` has a `createShape()` method that returns `Shape` by value. This causes **object slicing**: the derived part (`Circle` or `Rectangle`) is sliced off when the object is copied into a `Shape` value, and virtual method calls dispatch to the base class instead of the derived class.

The factory should return shapes by pointer (e.g., `std::unique_ptr<Shape>`) to preserve polymorphism.

Additionally, a `processShapes()` function stores shapes in a `std::vector<Shape>` (by value), which also causes slicing. It should use `std::vector<std::unique_ptr<Shape>>`.

## Expected Behavior

- `createShape("circle", 5.0)` returns a Circle with area ≈ 78.54 and name "Circle".
- `createShape("rectangle", 4.0, 6.0)` returns a Rectangle with area = 24.0 and name "Rectangle".
- Shapes stored in a vector maintain their polymorphic behavior.

## Actual Behavior

- All shapes returned from factory report name "Shape" and area 0 (base class defaults).
- Vector storage slices all derived data.

## Files

- `src/shapes.h` — Shape hierarchy declarations
- `src/shapes.cpp` — implementation
- `src/main.cpp` — test driver
