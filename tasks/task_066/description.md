# Feature: Implement Iterator for Custom Container

## Description

A `SkipList<T>` container class stores sorted unique elements. It supports `insert`, `contains`, `remove`, and `size` operations. However, it lacks iterator support, making it incompatible with range-for loops and STL algorithms like `std::find` and `std::count_if`.

### Feature Requirements

1. Add a forward iterator class (`SkipList<T>::iterator`) that:
   - Supports `operator*`, `operator->`, `operator++` (pre and post), `operator==`, `operator!=`
   - Is a proper forward iterator (with correct iterator traits/tags)

2. Add `begin()` and `end()` methods to `SkipList<T>`.

3. Add `const_iterator` with `cbegin()` and `cend()`.

4. The iterator should traverse elements in sorted order (the natural order of the skip list).

## Expected Behavior

```cpp
SkipList<int> sl;
sl.insert(30); sl.insert(10); sl.insert(20);
for (auto& val : sl) { std::cout << val << " "; }  // prints: 10 20 30
auto it = std::find(sl.begin(), sl.end(), 20);      // finds 20
```

## Files

- `src/skiplist.h` — SkipList implementation (no iterator support yet)
- `src/main.cpp` — test driver
