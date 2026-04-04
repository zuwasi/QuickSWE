# Bug Report: Reduction gives wrong results for certain array sizes

## Problem

The warp-level reduction kernel returns incorrect sums for arrays whose
element count is not divisible by 32. For "nice" sizes like 1024 or 2048 it
works perfectly. As soon as you try, say, 1000 or 1023 elements the total
is wrong — sometimes just slightly off, sometimes wildly wrong.

## How to Reproduce

```
./warp_reduce --size 1024 --seed 42   # works
./warp_reduce --size 1000 --seed 42   # wrong sum
./warp_reduce --size 100  --seed 42   # wrong sum
```

## Expected Behaviour

The GPU sum should match the CPU reference sum for any array length.

## Environment

- CUDA Toolkit 12.x, any GPU with compute capability >= 3.5
