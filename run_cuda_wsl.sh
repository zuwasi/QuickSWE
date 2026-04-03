#!/bin/bash
# QuickSWE CUDA Benchmark — runs inside WSL with CUDA toolkit
set -e

# Ensure CUDA and npm (for amp/claude) are on PATH
export PATH="/usr/local/cuda/bin:/mnt/c/Users/danie/AppData/Roaming/npm:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"

PROJ_DIR="/mnt/c/Amp_demos/QuickSWE"
cd "$PROJ_DIR"

echo "============================================"
echo "  QuickSWE CUDA Benchmark (WSL)"
echo "============================================"
echo "nvcc: $(nvcc --version 2>&1 | tail -1)"
echo "amp:  $(which amp)"
echo "claude: $(which claude)"
echo "Python: $(python3 --version)"
echo ""

# Verify agents work
amp --version 2>&1 | head -1 || { echo "ERROR: amp not working"; exit 1; }
claude --version 2>&1 | head -1 || { echo "ERROR: claude not working"; exit 1; }

CUDA_TASKS="task_056,task_057,task_058,task_069,task_070,task_071,task_072,task_073"
RUNS=3
TIMEOUT=600

for RUN in $(seq 1 $RUNS); do
    # Alternate agent order
    if [ $((RUN % 2)) -eq 1 ]; then
        AGENTS="amp claude"
    else
        AGENTS="claude amp"
    fi
    
    for AGENT in $AGENTS; do
        echo ""
        echo "============================================"
        echo "=== RUN $RUN/$RUNS | $AGENT | CUDA ==="
        echo "============================================"
        
        python3 "$PROJ_DIR/_cuda_runner.py" "$AGENT" "$RUN" "$CUDA_TASKS" "$TIMEOUT"
    done
    
    if [ "$RUN" -lt "$RUNS" ]; then
        echo "Pausing 30s..."
        sleep 30
    fi
done

echo ""
echo "============================================"
echo "  CUDA RUNS COMPLETE"
echo "============================================"
echo "Now run from Windows: python dashboard.py"
