import sys, os
sys.path.insert(0, r"C:\Amp_demos\QuickSWE")
os.chdir(r"C:\Amp_demos\QuickSWE")
os.environ["PATH"] = r"C:\Users\danie\AppData\Roaming\npm;" + os.environ["PATH"]

from _cuda_runner import *
from pathlib import Path
from datetime import datetime
import json, subprocess

CUDA_TASKS = [f"task_{i:03d}" for i in range(76, 101)]
TIMEOUT = 600

for run_idx in range(1, 4):
    print(f"\n=== CLAUDE CUDA RUN {run_idx}/3 ===")
    results = []
    for i, tid in enumerate(CUDA_TASKS, 1):
        print(f"  [{i}/{len(CUDA_TASKS)}] {tid} ...", end=" ", flush=True)
        r = run_task(Path(f"tasks/{tid}"), "claude", timeout=TIMEOUT)
        status = "PASS" if r["resolved"] else "FAIL"
        reg = " REG!" if r.get("regression") else ""
        print(f"{status}{reg} ({r['time_seconds']}s)")
        results.append(r)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(f"results/claude_cuda_run{run_idx}_{ts}.json")
    with open(out_path, "w") as f:
        json.dump({"agent": "claude", "run": run_idx, "timestamp": ts, "results": results}, f, indent=2)
    resolved = sum(1 for r in results if r["resolved"])
    print(f"  -> {resolved}/{len(results)} | Saved: {out_path.name}")

print("\nAll 3 Claude CUDA runs complete!")
