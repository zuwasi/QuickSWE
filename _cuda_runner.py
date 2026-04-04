"""CUDA task runner — invoked by run_cuda_wsl.sh."""
import json, sys, time, threading, os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import run_task

agent = sys.argv[1]
run_idx = sys.argv[2]
task_list = sys.argv[3]
timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 600

tasks = task_list.split(",")

stop = threading.Event()
def heartbeat():
    while not stop.is_set():
        print(".", end="", flush=True)
        stop.wait(15)

results = []
for i, tid in enumerate(tasks, 1):
    stop.clear()
    t = threading.Thread(target=heartbeat, daemon=True)
    t.start()
    print(f"  [{i}/{len(tasks)}] {tid} ", end="", flush=True)
    r = run_task(Path(f"tasks/{tid}"), agent, timeout=timeout)
    stop.set()
    status = "PASS" if r["resolved"] else "FAIL"
    reg = " REG!" if r.get("regression") else ""
    print(f" {status}{reg} ({r['time_seconds']}s)")
    results.append(r)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_agent = agent.replace("-", "_")
out_path = Path(f"results/{safe_agent}_cuda_run{run_idx}_{ts}.json")
out_path.parent.mkdir(exist_ok=True)
with open(out_path, "w") as f:
    json.dump({"agent": agent, "timestamp": ts, "results": results}, f, indent=2)
resolved = sum(1 for r in results if r["resolved"])
print(f"  -> {resolved}/{len(results)} | Saved: {out_path.name}")
