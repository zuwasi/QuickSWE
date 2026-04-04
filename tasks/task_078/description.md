# Bug Report: Image convolution produces wrong results at tile boundaries

## Problem

Our CUDA 2D convolution kernel gives wrong results. The output looks
correct in the center of large images but goes badly wrong near tile
boundaries and at the edges of the image. A 3×3 box blur produces visible
seam artifacts every TILE_SIZE pixels. A 5×5 Gaussian is even worse.

## How to Reproduce

```
./conv2d --width 64  --height 64  --radius 1 --seed 42   # 3x3, mostly OK
./conv2d --width 100 --height 100 --radius 1 --seed 42   # seams visible
./conv2d --width 64  --height 64  --radius 2 --seed 42   # 5x5, very wrong
```

## Expected Behaviour

GPU-convolved output should match the CPU reference within floating-point
tolerance for any image size and kernel radius.

## Environment

- CUDA Toolkit 12.x, any GPU with compute capability >= 3.5
