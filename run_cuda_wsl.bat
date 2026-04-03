@echo off
title QuickSWE CUDA Benchmark (via WSL)
color 0E
echo.
echo  ================================================================
echo    QuickSWE CUDA Benchmark — running via WSL
echo  ================================================================
echo.
echo  This will run 8 CUDA tasks x 3 runs x 2 agents inside WSL
echo  where nvcc is available.
echo.
echo  Estimated time: 2-3 hours
echo.
pause

wsl -- bash /mnt/c/Amp_demos/QuickSWE/run_cuda_wsl.sh

echo.
echo  Generating dashboard...
cd /d "C:\Amp_demos\QuickSWE"
python dashboard.py

echo.
echo  ================================================================
echo    CUDA BENCHMARK COMPLETE
echo  ================================================================
pause
