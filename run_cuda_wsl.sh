#!/bin/bash
# QuickSWE CUDA Benchmark — 3 agents: amp (smart), amp-deep, claude
set -e

export PATH="/usr/local/cuda/bin:/mnt/c/Users/danie/AppData/Roaming/npm:/usr/bin:/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"

PROJ_DIR="/mnt/c/Amp_demos/QuickSWE"
cd "$PROJ_DIR"

echo "============================================"
echo "  QuickSWE CUDA Benchmark (WSL)"
echo "  3 agents: amp | amp-deep | claude"
echo "============================================"
echo "nvcc: $(nvcc --version 2>&1 | tail -1)"
echo ""

# All 20 CUDA tasks
ALL_CUDA="task_056,task_057,task_058,task_069,task_070,task_071,task_072,task_073,task_074,task_075,task_076,task_077,task_078,task_079,task_080,task_081,task_082,task_083,task_084,task_085"
RUNS=2
TIMEOUT=600
AGENTS="amp amp-deep claude"

for RUN in $(seq 1 $RUNS); do
    for AGENT in $AGENTS; do
        echo ""
        echo "============================================"
        echo "=== RUN $RUN/$RUNS | $AGENT | CUDA (20 tasks) ==="
        echo "============================================"
        
        python3 "$PROJ_DIR/_cuda_runner.py" "$AGENT" "$RUN" "$ALL_CUDA" "$TIMEOUT"
    done
    
    if [ "$RUN" -lt "$RUNS" ]; then
        echo "Pausing 30s..."
        sleep 30
    fi
done

echo ""
echo "============================================"
echo "  CUDA RUNS COMPLETE — 3 agents compared"
echo "============================================"
echo "Run from Windows: python dashboard.py"
