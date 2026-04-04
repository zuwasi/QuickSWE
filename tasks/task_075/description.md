# Bug Report: Multi-stream processing produces duplicates and occasional garbage values

## Problem

We split an array across two CUDA streams for parallel processing (each
element is squared, then the two halves are merged). The merged result
contains duplicate values near the partition boundary and sometimes has
garbage (very large or negative numbers) scattered throughout.

## How to Reproduce

```
./multi_stream --size 1024 --seed 42   # sometimes looks OK
./multi_stream --size 1000 --seed 42   # duplicates near midpoint
./multi_stream --size 500  --seed 7    # garbage values appear
```

## Expected Behaviour

Every element should appear exactly once in the output and equal `input[i] * input[i]`.

## Environment

- CUDA Toolkit 12.x, any GPU (uses 2 streams on one GPU)
