@echo off
title QuickSWE - Quick Test (3 tasks, 1 run)
color 0B
echo.
echo  ================================================================
echo    QuickSWE - QUICK TEST
echo  ================================================================
echo.
echo  This will:
echo    1. Clean previous results
echo    2. Run both agents on 3 tasks (1 run each)
echo    3. Generate the visual dashboard
echo.
echo  Estimated time: 15-30 minutes
echo.
pause

cd /d "C:\Amp_demos\QuickSWE"

echo.
echo  [Step 1/3] Cleaning previous results...
if exist results\*.json del /q results\*.json
if exist results\*.html del /q results\*.html
echo  Done.

echo.
echo  [Step 2/3] Running quick test...
python multi_runner.py --runs 1 --agent both --tasks task_001,task_005,task_016,task_021 --pause 10 --timeout 300

echo.
echo  [Step 3/3] Generating dashboard...
python dashboard.py

echo.
echo  ================================================================
echo    QUICK TEST COMPLETE
echo  ================================================================
echo.
pause
