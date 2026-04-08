import json

with open("results/claude_run2_20260408_015455.json") as f:
    data = json.load(f)

for r in data["results"][:5]:
    tid = r["task_id"]
    err = r.get("error", "none")
    res = r["resolved"]
    t = r["time_seconds"]
    out = (r.get("agent_output") or "")[:200]
    print(f"{tid}: resolved={res} error={err} time={t}s")
    if out:
        print(f"  output: {out}")
    print()
