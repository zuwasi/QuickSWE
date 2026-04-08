"""Multi-run benchmark runner for statistical reliability.

Runs the benchmark N times, alternates agent order each round,
and produces an aggregated summary with per-task resolve rates,
timing statistics, and consistency scores.
"""

import argparse
import json
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from runner import RESULTS_DIR, discover_tasks, load_task_metadata, run_task


# ── progress tracker ─────────────────────────────────────────────────────────

class ProgressTracker:
    """Live progress widget for benchmark runs."""

    def __init__(self, total_runs: int, total_tasks: int, agents: list[str]):
        self.total_runs = total_runs
        self.total_tasks = total_tasks
        self.agents = agents
        self.total_invocations = total_runs * total_tasks * len(agents)
        self.completed = 0
        self.resolved = 0
        self.failed = 0
        self.errors = 0
        self.start_time = time.perf_counter()
        self._agent_resolved: dict[str, int] = defaultdict(int)
        self._agent_total: dict[str, int] = defaultdict(int)

    def update(self, result: dict, agent: str):
        self.completed += 1
        self._agent_total[agent] += 1
        if result["resolved"]:
            self.resolved += 1
            self._agent_resolved[agent] += 1
        elif result.get("error"):
            self.errors += 1
        else:
            self.failed += 1

    def _format_eta(self) -> str:
        elapsed = time.perf_counter() - self.start_time
        if self.completed == 0:
            return "calculating..."
        rate = elapsed / self.completed
        remaining = (self.total_invocations - self.completed) * rate
        eta = timedelta(seconds=int(remaining))
        return str(eta)

    def _bar(self, width: int = 30) -> str:
        pct = self.completed / self.total_invocations if self.total_invocations else 0
        filled = int(width * pct)
        return f"[{'#' * filled}{'-' * (width - filled)}]"

    def display(self):
        pct = (self.completed / self.total_invocations * 100) if self.total_invocations else 0
        elapsed = timedelta(seconds=int(time.perf_counter() - self.start_time))
        eta = self._format_eta()
        bar = self._bar()

        agent_stats = " | ".join(
            f"{a}: {self._agent_resolved[a]}/{self._agent_total[a]}"
            for a in self.agents if self._agent_total[a] > 0
        )

        print(f"\n  {bar} {pct:5.1f}%  "
              f"({self.completed}/{self.total_invocations})  "
              f"OK:{self.resolved} FAIL:{self.failed} ERR:{self.errors}  "
              f"Elapsed: {elapsed}  ETA: {eta}")
        if agent_stats:
            print(f"  Agent resolve: {agent_stats}")

# ── graceful shutdown ────────────────────────────────────────────────────────

_interrupted = False


def _handle_sigint(sig, frame):
    global _interrupted
    if _interrupted:
        print("\nForced exit.")
        sys.exit(1)
    _interrupted = True
    print("\n[!] Ctrl+C received -- finishing current task then saving results...")


signal.signal(signal.SIGINT, _handle_sigint)


# ── individual run persistence ───────────────────────────────────────────────

def save_run_results(agent: str, run_num: int, records: list[dict]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{agent}_run{run_num}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "agent": agent,
            "run": run_num,
            "timestamp": ts,
            "results": records,
        }, f, indent=2)
    return path


# ── aggregation ──────────────────────────────────────────────────────────────

def aggregate(raw: dict[str, list[list[dict]]],
              task_dirs: list[Path]) -> dict:
    """Build the aggregate summary from raw[agent] = [ [run1_records], … ]."""

    meta_cache: dict[str, dict] = {}
    for td in task_dirs:
        meta_cache[td.name] = load_task_metadata(td)

    agent_summaries: dict[str, dict] = {}
    per_task: dict[str, dict[str, dict]] = defaultdict(dict)
    by_category: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(
        lambda: {"resolved": 0, "total": 0}))
    by_difficulty: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(
        lambda: {"resolved": 0, "total": 0}))

    for agent, runs in raw.items():
        all_times: list[float] = []
        total_resolved = 0
        total_regressions = 0
        total_count = 0

        task_runs: dict[str, list[dict]] = defaultdict(list)
        for run_records in runs:
            for rec in run_records:
                task_runs[rec["task_id"]].append(rec)

        for task_id, records in sorted(task_runs.items()):
            n = len(records)
            resolved_count = sum(1 for r in records if r["resolved"])
            regression_count = sum(1 for r in records if r["regression"])
            times = [r["time_seconds"] for r in records if r["agent_completed"]]

            # consistency: fraction of runs with the same resolved outcome
            if n > 0:
                majority = max(resolved_count, n - resolved_count)
                consistency = round(majority / n, 4)
            else:
                consistency = 0.0

            meta = meta_cache.get(task_id, {})
            cat = meta.get("category", "unknown")
            diff = meta.get("difficulty", "unknown")

            per_task[task_id][agent] = {
                "resolve_rate": round(resolved_count / n, 4) if n else 0,
                "regression_rate": round(regression_count / n, 4) if n else 0,
                "avg_time": round(sum(times) / len(times), 2) if times else 0,
                "min_time": round(min(times), 2) if times else 0,
                "max_time": round(max(times), 2) if times else 0,
                "consistency_score": consistency,
                "runs": n,
                "category": cat,
                "difficulty": diff,
            }

            total_resolved += resolved_count
            total_regressions += regression_count
            total_count += n
            all_times.extend(times)

            by_category[agent][cat]["resolved"] += resolved_count
            by_category[agent][cat]["total"] += n
            by_difficulty[agent][diff]["resolved"] += resolved_count
            by_difficulty[agent][diff]["total"] += n

        agent_summaries[agent] = {
            "total_resolve_rate": round(total_resolved / total_count, 4) if total_count else 0,
            "avg_time": round(sum(all_times) / len(all_times), 2) if all_times else 0,
            "regression_rate": round(total_regressions / total_count, 4) if total_count else 0,
            "total_resolved": total_resolved,
            "total_tasks": total_count,
        }

    # Convert category / difficulty dicts to serialisable form with rates
    def _rate_dict(d):
        out = {}
        for agent, cats in d.items():
            out[agent] = {}
            for key, vals in cats.items():
                t = vals["total"]
                out[agent][key] = {
                    "resolve_rate": round(vals["resolved"] / t, 4) if t else 0,
                    "resolved": vals["resolved"],
                    "total": t,
                }
        return out

    return {
        "per_task": dict(per_task),
        "overall": agent_summaries,
        "by_category": _rate_dict(by_category),
        "by_difficulty": _rate_dict(by_difficulty),
        "raw_runs": {
            agent: [[r for r in run] for run in runs]
            for agent, runs in raw.items()
        },
    }


def save_aggregate(agg: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"aggregate_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(agg, f, indent=2)
    return path


# ── console summary ─────────────────────────────────────────────────────────

def print_aggregate_summary(agg: dict):
    sep = "=" * 90
    print(f"\n{sep}")
    print("AGGREGATE BENCHMARK RESULTS")
    print(sep)

    # Per-task table
    agents = sorted(agg["overall"].keys())
    header = f"{'Task':<20}"
    for a in agents:
        header += f" {'Resolve':>8} {'AvgT(s)':>8} {'Consist':>8}"
    print(header)
    print("-" * len(header))

    for task_id in sorted(agg["per_task"]):
        row = f"{task_id:<20}"
        for a in agents:
            stats = agg["per_task"][task_id].get(a)
            if stats:
                rr = f"{stats['resolve_rate']:.0%}"
                at = f"{stats['avg_time']:.1f}"
                cs = f"{stats['consistency_score']:.0%}"
                row += f" {rr:>8} {at:>8} {cs:>8}"
            else:
                row += f" {'N/A':>8} {'N/A':>8} {'N/A':>8}"
        print(row)

    # Overall
    print(f"\n{sep}")
    print(f"{'Agent':<10} {'Resolve Rate':<14} {'Regression':<12} {'Avg Time(s)':<12}")
    print("-" * 48)
    for a in agents:
        o = agg["overall"][a]
        print(f"{a:<10} {o['total_resolve_rate']:.1%}  ({o['total_resolved']}/{o['total_tasks']})"
              f"   {o['regression_rate']:.1%}         {o['avg_time']:.1f}")

    # By category
    if any(agg["by_category"].values()):
        print(f"\n{sep}")
        print("BY CATEGORY")
        print("-" * 48)
        cats = sorted({c for adata in agg["by_category"].values() for c in adata})
        for cat in cats:
            parts = []
            for a in agents:
                info = agg["by_category"].get(a, {}).get(cat)
                if info:
                    parts.append(f"{a}: {info['resolve_rate']:.0%}")
            print(f"  {cat:<18} {', '.join(parts)}")

    # By difficulty
    if any(agg["by_difficulty"].values()):
        print(f"\n{sep}")
        print("BY DIFFICULTY")
        print("-" * 48)
        diffs = sorted({d for adata in agg["by_difficulty"].values() for d in adata})
        for diff in diffs:
            parts = []
            for a in agents:
                info = agg["by_difficulty"].get(a, {}).get(diff)
                if info:
                    parts.append(f"{a}: {info['resolve_rate']:.0%}")
            print(f"  {diff:<18} {', '.join(parts)}")

    print(sep)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run the benchmark multiple times for statistical reliability",
    )
    parser.add_argument("--runs", type=int, default=3,
                        help="Number of full runs (default: 3)")
    parser.add_argument("--agent", choices=["amp", "amp-deep3", "claude", "both", "deep3-vs-claude"],
                        default="both",
                        help="Which agent(s) to run (default: both)")
    parser.add_argument("--tasks", default="all",
                        help="Comma-separated task IDs or 'all' (default: all)")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Per-task timeout in seconds (default: 300)")
    parser.add_argument("--pause", type=int, default=30,
                        help="Seconds to pause between runs (default: 30)")
    args = parser.parse_args()

    if args.agent == "both":
        agents = ["amp", "claude"]
    elif args.agent == "deep3-vs-claude":
        agents = ["amp-deep3", "claude"]
    else:
        agents = [args.agent]
    tasks = discover_tasks(args.tasks)

    if not tasks:
        print("No tasks found.")
        sys.exit(1)

    total_runs = args.runs
    total_agent_tasks = len(tasks) * len(agents)
    print(f"Configuration: {total_runs} run(s)  |  {len(tasks)} task(s)  |  "
          f"Agents: {', '.join(agents)}  |  Timeout: {args.timeout}s  |  "
          f"Pause: {args.pause}s")
    print(f"Total individual task invocations: {total_runs * total_agent_tasks}\n")

    # raw[agent] -> list of per-run record lists
    raw: dict[str, list[list[dict]]] = {a: [] for a in agents}
    completed_runs = 0
    progress = ProgressTracker(total_runs, len(tasks), agents)

    for run_idx in range(1, total_runs + 1):
        if _interrupted:
            break

        # Alternate which agent goes first each round
        ordered_agents = agents if run_idx % 2 == 1 else list(reversed(agents))

        for agent in ordered_agents:
            if _interrupted:
                break

            print(f"\n{'=' * 60}")
            print(f"=== RUN {run_idx}/{total_runs} === Agent: {agent} ===")
            print(f"{'=' * 60}")

            records: list[dict] = []
            for task_num, task_dir in enumerate(tasks, 1):
                if _interrupted:
                    break

                print(f"  [{task_num}/{len(tasks)}] {task_dir.name} ...", end=" ", flush=True)
                result = run_task(task_dir, agent, args.timeout)

                if result["resolved"]:
                    status = "[OK] RESOLVED"
                elif result.get("error"):
                    status = f"[X] ERROR ({result['error']})"
                else:
                    status = "[X] FAILED"

                reg = " [!]REGRESSION" if result["regression"] else ""
                t = f" ({result['time_seconds']:.1f}s)"
                print(f"{status}{reg}{t}")
                records.append(result)
                progress.update(result, agent)
                progress.display()

            # Save this run
            if records:
                path = save_run_results(agent, run_idx, records)
                print(f"  -> Saved: {path}")
                raw[agent].append(records)

        completed_runs += 1

        # Pause between runs (not after the last one)
        if run_idx < total_runs and not _interrupted and args.pause > 0:
            print(f"\nPausing {args.pause}s before next run...")
            for remaining in range(args.pause, 0, -1):
                if _interrupted:
                    break
                time.sleep(1)

    # Aggregate and save
    has_data = any(runs for runs in raw.values())
    if not has_data:
        print("\nNo results collected.")
        sys.exit(1)

    print("\nAggregating results...")
    agg = aggregate(raw, tasks)
    agg_path = save_aggregate(agg)
    print(f"Aggregate saved: {agg_path}")

    print_aggregate_summary(agg)

    if _interrupted:
        print(f"\n[!] Run was interrupted after {completed_runs}/{total_runs} complete round(s).")


if __name__ == "__main__":
    main()
