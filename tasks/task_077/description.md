# Bug Report: Radix sort corrupts data

## Problem

The CUDA radix sort loses some elements and duplicates others. After sorting,
the array has the same length but some values appear twice while others are
missing entirely. The overall ordering is roughly correct (small values near
the start) but the exact contents are wrong.

## How to Reproduce

```
./radix_sort --size 1024 --seed 42   # elements missing / duplicated
./radix_sort --size 100  --seed 7    # same problem, easier to inspect
```

## Expected Behaviour

The GPU-sorted output should contain exactly the same elements as the input,
in ascending order, matching the CPU reference sort.

## Environment

- CUDA Toolkit 12.x, any GPU with compute capability >= 3.5
