@echo off
title QuickSWE Benchmark
color 0A
echo.
echo  ================================================================
echo    QuickSWE - Benchmark Runner
echo  ================================================================
echo.
echo  This will:
echo    1. Clean previous results
echo    2. Run both agents on all 15 tasks (3 runs each)
echo    3. Generate the visual dashboard
echo.
echo  Estimated time: 4-5 hours
echo.
echo  Press Ctrl+C to cancel, or
pause

cd /d "C:\Amp_demos\QuickSWE"

echo.
echo  [Step 1/3] Cleaning previous results...
echo  -----------------------------------------
if exist results\*.json del /q results\*.json
if exist results\*.html del /q results\*.html
echo  Done.

echo.
echo  [Step 2/3] Running benchmark (3 runs, 15 tasks, both agents)...
echo  ----------------------------------------------------------------
python multi_runner.py --runs 3 --agent both --pause 30 --timeout 300
if errorlevel 1 (
    echo.
    echo  [!] Benchmark runner encountered an error.
    echo  Attempting to generate dashboard from partial results...
)

echo.
echo  [Step 3/3] Generating dashboard...
echo  ------------------------------------
python dashboard.py
if errorlevel 1 (
    echo  [!] Dashboard generation failed.
    pause
    exit /b 1
)

echo.
echo  ================================================================
echo    BENCHMARK COMPLETE
echo  ================================================================
echo.
echo  Dashboard opened in your browser.
echo  Results saved in: C:\Amp_demos\QuickSWE\results\
echo.
pause
