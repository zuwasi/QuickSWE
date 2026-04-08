#!/bin/bash
set -e
export PATH="/usr/local/cuda/bin:/mnt/c/Users/danie/AppData/Roaming/npm:/usr/bin:/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"

cd /mnt/c/Amp_demos/QuickSWE

echo "============================================"
echo "  Claude Code — CUDA Only (3 runs x 25 tasks)"
echo "============================================"
echo "nvcc: $(nvcc --version 2>&1 | tail -1)"
echo "claude: $(claude --version 2>&1)"
echo ""

ALL_CUDA="task_076,task_077,task_078,task_079,task_080,task_081,task_082,task_083,task_084,task_085,task_086,task_087,task_088,task_089,task_090,task_091,task_092,task_093,task_094,task_095,task_096,task_097,task_098,task_099,task_100"

for RUN in 1 2 3; do
    echo ""
    echo "============================================"
    echo "=== RUN $RUN/3 | claude | CUDA (25 tasks) ==="
    echo "============================================"
    python3 _cuda_runner.py claude "$RUN" "$ALL_CUDA" 600
    if [ "$RUN" -lt 3 ]; then
        echo "Pausing 30s..."
        sleep 30
    fi
done

echo ""
echo "============================================"
echo "  Claude CUDA RUNS COMPLETE"
echo "============================================"
