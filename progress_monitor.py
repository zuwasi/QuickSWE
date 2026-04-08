"""Floating progress monitor — reads the benchmark log file and shows live status."""

import glob
import os
import re
import sys
import time
from datetime import datetime, timedelta

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
LOG_PATTERN = os.path.join(os.path.dirname(__file__), "benchmark_run_*.log")

# Benchmark config: 3 runs × 100 tasks × 2 agents
TOTAL_RUNS = 3
TOTAL_TASKS = 100
AGENTS = ["amp-deep3", "claude"]
TOTAL_INVOCATIONS = TOTAL_RUNS * TOTAL_TASKS * len(AGENTS)


def parse_log(log_path: str) -> dict:
    """Parse the benchmark log and extract progress stats."""
    stats = {
        "completed": 0,
        "resolved": 0,
        "failed": 0,
        "errors": 0,
        "current_run": 0,
        "current_agent": "",
        "current_task": "",
        "last_line": "",
        "agent_resolved": {},
        "agent_total": {},
        "saved_runs": 0,
        "start_time": None,
    }

    current_agent = ""
    current_run = 0

    with open(log_path, encoding="utf-16", errors="replace") as f:
        for line in f:
            line = line.rstrip()

            # Detect start time
            m = re.match(r"Starting benchmark at (.+)", line)
            if m:
                try:
                    stats["start_time"] = datetime.strptime(
                        m.group(1).strip(), "%m/%d/%Y %H:%M:%S"
                    )
                except ValueError:
                    pass

            # Detect run/agent header
            m = re.match(r"=== RUN (\d+)/(\d+) === Agent: (\S+) ===", line)
            if m:
                current_run = int(m.group(1))
                current_agent = m.group(3)
                stats["current_run"] = current_run
                stats["current_agent"] = current_agent

            # Detect task result
            m = re.match(
                r"\s+\[(\d+)/(\d+)\]\s+(task_\d+)\s+\.\.\.\s+(.+)", line
            )
            if m:
                task_num = int(m.group(1))
                task_id = m.group(3)
                result_str = m.group(4)
                stats["completed"] += 1
                stats["current_task"] = task_id

                if current_agent not in stats["agent_total"]:
                    stats["agent_total"][current_agent] = 0
                    stats["agent_resolved"][current_agent] = 0
                stats["agent_total"][current_agent] += 1

                if "[OK] RESOLVED" in result_str:
                    stats["resolved"] += 1
                    stats["agent_resolved"][current_agent] += 1
                elif "ERROR" in result_str:
                    stats["errors"] += 1
                else:
                    stats["failed"] += 1

            # Detect saved run
            if "-> Saved:" in line:
                stats["saved_runs"] += 1

            if line.strip():
                stats["last_line"] = line.strip()

    return stats


def bar(pct: float, width: int = 40) -> str:
    filled = int(width * pct)
    return f"[{'█' * filled}{'░' * (width - filled)}]"


def display(stats: dict):
    os.system("cls" if os.name == "nt" else "clear")

    pct = stats["completed"] / TOTAL_INVOCATIONS if TOTAL_INVOCATIONS else 0
    now = datetime.now()

    # ETA calculation
    if stats["start_time"] and stats["completed"] > 0:
        elapsed = now - stats["start_time"]
        rate = elapsed.total_seconds() / stats["completed"]
        remaining = (TOTAL_INVOCATIONS - stats["completed"]) * rate
        eta = timedelta(seconds=int(remaining))
        elapsed_str = str(timedelta(seconds=int(elapsed.total_seconds())))
        eta_str = str(eta)
        finish_time = (now + eta).strftime("%H:%M:%S")
    else:
        elapsed_str = "..."
        eta_str = "calculating..."
        finish_time = "..."

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          QuickSWE v2 — Benchmark Progress Monitor          ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║                                                              ║")
    print(f"║  {bar(pct)}  {pct*100:5.1f}%               ║")
    print(f"║  {stats['completed']:>4} / {TOTAL_INVOCATIONS}  invocations complete                   ║")
    print(f"║                                                              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  ✓ Resolved: {stats['resolved']:<6}  "
          f"✗ Failed: {stats['failed']:<6}  "
          f"⚠ Errors: {stats['errors']:<5}    ║")
    print(f"║  Run: {stats['current_run']}/{TOTAL_RUNS}        "
          f"Agent: {stats['current_agent']:<15}              ║")
    print(f"║  Last task: {stats['current_task']:<20}                        ║")
    print(f"║  Saved runs: {stats['saved_runs']}/{TOTAL_RUNS * len(AGENTS)}                                          ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Elapsed: {elapsed_str:<14}  "
          f"ETA: {eta_str:<14}              ║")
    print(f"║  Est. finish: {finish_time:<12}                                ║")
    print("╠══════════════════════════════════════════════════════════════╣")

    # Per-agent stats
    for agent in AGENTS:
        total = stats["agent_total"].get(agent, 0)
        resolved = stats["agent_resolved"].get(agent, 0)
        if total > 0:
            agent_pct = resolved / total * 100
            agent_bar = bar(resolved / total, 20)
            print(f"║  {agent:<12} {agent_bar} "
                  f"{resolved:>3}/{total:<3} ({agent_pct:4.1f}%)        ║")
        else:
            print(f"║  {agent:<12} [░░░░░░░░░░░░░░░░░░░░]   0/0   (  --)        ║")

    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Last: {stats['last_line'][:54]:<54} ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n  Refreshing every 10s...  Press Ctrl+C to exit monitor.")


def main():
    logs = sorted(glob.glob(LOG_PATTERN))
    if not logs:
        print("No benchmark log found. Is the benchmark running?")
        sys.exit(1)

    log_path = logs[-1]  # latest log
    print(f"Monitoring: {log_path}")

    try:
        while True:
            stats = parse_log(log_path)
            display(stats)
            if stats["completed"] >= TOTAL_INVOCATIONS:
                print("\n  ✅ Benchmark complete!")
                break
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
