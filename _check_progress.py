from progress_monitor import parse_log, TOTAL_INVOCATIONS, AGENTS
import glob

log = sorted(glob.glob("benchmark_run_*.log"))[-1]
s = parse_log(log)
pct = s["completed"] / TOTAL_INVOCATIONS * 100
print(f"Progress: {s['completed']}/{TOTAL_INVOCATIONS} ({pct:.1f}%)")
print(f"Resolved: {s['resolved']}  Failed: {s['failed']}  Errors: {s['errors']}")
print(f"Run {s['current_run']}/3  Agent: {s['current_agent']}  Task: {s['current_task']}")
for a in AGENTS:
    t = s["agent_total"].get(a, 0)
    r = s["agent_resolved"].get(a, 0)
    if t:
        print(f"  {a}: {r}/{t} ({r/t*100:.1f}%)")
