"""Benchmark runner: orchestrates Amp and Claude Code CLI on coding tasks."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

TASKS_DIR = Path(__file__).parent / "tasks"
RESULTS_DIR = Path(__file__).parent / "results"

PROMPT_TEMPLATE = (
    "Fix the issue described below. "
    "Only modify files in the current directory.\n\n"
    "CRITICAL SAFETY RULES:\n"
    "- NEVER delete, remove, or modify ANY files outside this working directory\n"
    "- NEVER use rm -rf, Remove-Item -Recurse, rmdir, or shutil.rmtree on any path outside '.'\n"
    "- NEVER access parent directories (..) or absolute paths like C:\\\n"
    "- Only edit files in src/ and create new files in the current directory\n\n"
    "{issue}"
)


# ── pytest helpers ───────────────────────────────────────────────────────────

def _run_pytest(work_dir: Path, test_dir: Path, marker: str | None = None,
                timeout: int = 120) -> dict:
    """Run pytest and return structured results."""
    cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"]
    if marker:
        cmd += ["-m", marker]

    try:
        proc = subprocess.run(
            cmd, cwd=str(work_dir), capture_output=True, text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"passed": False, "detail": "pytest timed out", "returncode": -1}

    passed = proc.returncode == 0
    return {
        "passed": passed,
        "detail": proc.stdout + proc.stderr,
        "returncode": proc.returncode,
    }


def run_fail_to_pass(work_dir: Path, test_dir: Path) -> dict:
    return _run_pytest(work_dir, test_dir, marker="fail_to_pass")


def run_pass_to_pass(work_dir: Path, test_dir: Path) -> dict:
    return _run_pytest(work_dir, test_dir, marker="not fail_to_pass")


def run_all_tests(work_dir: Path, test_dir: Path) -> dict:
    return _run_pytest(work_dir, test_dir)


# ── task discovery ───────────────────────────────────────────────────────────

def discover_tasks(task_filter: str) -> list[Path]:
    """Return sorted list of task directories matching the filter."""
    if not TASKS_DIR.is_dir():
        print(f"ERROR: tasks directory not found: {TASKS_DIR}")
        sys.exit(1)

    all_tasks = sorted(
        p for p in TASKS_DIR.iterdir()
        if p.is_dir() and (p / "description.md").exists()
    )

    if task_filter == "all":
        return all_tasks

    requested = {t.strip() for t in task_filter.split(",")}
    matched = [p for p in all_tasks if p.name in requested]
    missing = requested - {p.name for p in matched}
    if missing:
        print(f"WARNING: tasks not found: {', '.join(sorted(missing))}")
    return matched


def load_task_metadata(task_dir: Path) -> dict:
    meta_path = task_dir / "metadata.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_description(task_dir: Path) -> str:
    with open(task_dir / "description.md", encoding="utf-8") as f:
        return f.read()


# ── agent invocation ─────────────────────────────────────────────────────────

def _write_guardrail_files(work_dir: Path):
    """Write CLAUDE.md and AGENTS.md guardrails into the work directory."""
    guardrail = (
        "# BENCHMARK TASK — SAFETY RULES\n\n"
        "You are running inside an isolated benchmark workspace.\n\n"
        "## CRITICAL — DO NOT VIOLATE\n"
        "- ONLY modify files inside THIS directory\n"
        "- NEVER access, delete, or modify files outside this directory\n"
        "- NEVER use absolute paths (C:\\, /home/, etc.)\n"
        "- NEVER navigate to parent directories (..)\n"
        "- NEVER run rm -rf, Remove-Item -Recurse, rmdir, or shutil.rmtree "
        "on any path outside '.'\n"
        "- NEVER delete directories you did not create\n"
    )
    (work_dir / "CLAUDE.md").write_text(guardrail, encoding="utf-8")
    (work_dir / "AGENTS.md").write_text(guardrail, encoding="utf-8")


def invoke_agent(agent: str, prompt: str, work_dir: Path,
                 timeout: int) -> tuple[float, bool, str]:
    """Invoke an agent CLI and return (elapsed_seconds, success, output)."""
    # Write guardrail files so agents see safety rules
    _write_guardrail_files(work_dir)

    # Write prompt to a temp file to avoid shell escaping issues
    prompt_file = work_dir / "_prompt.txt"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    if agent == "amp":
        cmd = ["amp", "--dangerously-allow-all", "-x", prompt]
    elif agent == "amp-deep":
        cmd = ["amp", "--dangerously-allow-all", "--mode", "deep", "-x", prompt]
    elif agent == "amp-deep3":
        # Write temp settings for deep³ (xhigh reasoning)
        settings_file = work_dir / "_amp_settings.json"
        with open(settings_file, "w") as sf:
            json.dump({"amp.agent.deepReasoningEffort": "xhigh"}, sf)
        cmd = ["amp", "--dangerously-allow-all", "--mode", "deep",
               "--settings-file", str(settings_file), "-x", prompt]
    elif agent == "amp-rush":
        cmd = ["amp", "--dangerously-allow-all", "--mode", "rush", "-x", prompt]
    elif agent == "claude":
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--allow-dangerously-skip-permissions",
            "-p", prompt,
        ]
    else:
        raise ValueError(f"Unknown agent: {agent}")

    env = os.environ.copy()
    env["CLAUDE_CODE_SKIP_PERMISSIONS"] = "1"

    # Use shell=True on Windows for .cmd resolution
    use_shell = (os.name == "nt")

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, cwd=str(work_dir), capture_output=True, text=True,
            timeout=timeout, env=env, shell=use_shell,
            encoding="utf-8", errors="replace",
        )
        elapsed = time.perf_counter() - start
        output = (proc.stdout or "") + (proc.stderr or "")
        return elapsed, True, output
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return elapsed, False, f"Agent timed out after {timeout}s"
    except FileNotFoundError:
        elapsed = time.perf_counter() - start
        return elapsed, False, f"Agent CLI '{agent}' not found on PATH"


# ── single-task execution ───────────────────────────────────────────────────

def run_task(task_dir: Path, agent: str, timeout: int) -> dict:
    """Run a single task with a single agent and return the result record."""
    task_id = task_dir.name
    metadata = load_task_metadata(task_dir)
    description = load_description(task_dir)
    prompt = PROMPT_TEMPLATE.format(issue=description)

    src_dir = task_dir / "src"
    test_dir = task_dir / "tests"

    if not src_dir.is_dir():
        return _error_record(task_id, agent, metadata, "src/ directory missing")
    if not test_dir.is_dir():
        return _error_record(task_id, agent, metadata, "tests/ directory missing")

    # Prepare isolated working directory
    tmp_root = tempfile.mkdtemp(prefix=f"bench_{task_id}_{agent}_")
    work_dir = Path(tmp_root)

    # Snapshot critical directories before agent runs
    _protected_dirs = [
        Path(r"C:\parasoft"),
        Path(r"C:\Amp_demos"),
        Path(r"C:\Amp_demos_RECOVERED"),
        Path.home(),
    ]
    _pre_snapshot = {
        str(d): set(p.name for p in d.iterdir()) if d.exists() else set()
        for d in _protected_dirs
    }

    try:
        # Copy src/ directory preserving structure (tests import from src.module)
        work_src_dir = work_dir / "src"
        shutil.copytree(src_dir, work_src_dir)

        # Copy tests alongside source so pytest can find imports
        work_test_dir = work_dir / "tests"
        shutil.copytree(test_dir, work_test_dir)

        # Copy description so the agent can read it in context
        shutil.copy2(task_dir / "description.md", work_dir / "description.md")

        # Sanity: fail_to_pass tests should fail before the fix
        pre_check = run_fail_to_pass(work_dir, work_test_dir)
        if pre_check["passed"]:
            return _error_record(
                task_id, agent, metadata,
                "fail_to_pass tests already pass before agent ran (bad task)",
            )

        # Invoke agent
        elapsed, agent_ok, agent_output = invoke_agent(
            agent, prompt, work_dir, timeout,
        )

        # Safety check: verify no protected directories were damaged
        for d_str, pre_items in _pre_snapshot.items():
            d = Path(d_str)
            if d.exists():
                post_items = set(p.name for p in d.iterdir())
                deleted = pre_items - post_items
                if deleted:
                    print(f"\n  [!!!] SAFETY ALERT: {agent} deleted items from "
                          f"{d}: {deleted}", file=sys.stderr)
            elif pre_items:
                print(f"\n  [!!!] SAFETY ALERT: {agent} deleted entire "
                      f"directory {d}!", file=sys.stderr)

        # Post-fix: check fail_to_pass
        post_f2p = run_fail_to_pass(work_dir, work_test_dir)
        resolved = post_f2p["passed"]

        # Post-fix: check pass_to_pass (regressions)
        post_p2p = run_pass_to_pass(work_dir, work_test_dir)
        regression = not post_p2p["passed"]

        return {
            "task_id": task_id,
            "agent": agent,
            "category": metadata.get("category", "unknown"),
            "difficulty": metadata.get("difficulty", "unknown"),
            "resolved": resolved,
            "regression": regression,
            "time_seconds": round(elapsed, 2),
            "agent_completed": agent_ok,
            "fail_to_pass": _summarise(post_f2p),
            "pass_to_pass": _summarise(post_p2p),
            "agent_output": agent_output[:2000] if agent_output else "",
            "error": None,
        }
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def _error_record(task_id, agent, metadata, message):
    return {
        "task_id": task_id,
        "agent": agent,
        "category": metadata.get("category", "unknown"),
        "difficulty": metadata.get("difficulty", "unknown"),
        "resolved": False,
        "regression": False,
        "time_seconds": 0,
        "agent_completed": False,
        "fail_to_pass": None,
        "pass_to_pass": None,
        "error": message,
    }


def _summarise(result: dict) -> dict:
    return {"passed": result["passed"], "returncode": result["returncode"]}


# ── results persistence ─────────────────────────────────────────────────────

def save_results(agent: str, records: list[dict]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{agent}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"agent": agent, "timestamp": ts, "results": records},
                  f, indent=2)
    return path


# ── console summary ─────────────────────────────────────────────────────────

def print_summary(all_records: dict[str, list[dict]]):
    """Print a compact comparison table to the console."""
    sep = "-" * 80
    print(f"\n{sep}")
    print("BENCHMARK RESULTS")
    print(sep)

    # Per-task table
    header = f"{'Task':<20} {'Agent':<8} {'Resolved':<10} {'Regress':<9} {'Time(s)':<10}"
    print(header)
    print("-" * len(header))
    for agent, records in sorted(all_records.items()):
        for r in records:
            res = "YES" if r["resolved"] else "NO"
            reg = "YES" if r["regression"] else "-"
            t = f"{r['time_seconds']:.1f}"
            err = f"  ERR: {r['error']}" if r.get("error") else ""
            print(f"{r['task_id']:<20} {agent:<8} {res:<10} {reg:<9} {t:<10}{err}")

    # Totals per agent
    print(f"\n{sep}")
    print(f"{'Agent':<10} {'Resolved':<12} {'Regressions':<14} {'Avg Time(s)':<12}")
    print("-" * 48)
    for agent, records in sorted(all_records.items()):
        total = len(records)
        res = sum(1 for r in records if r["resolved"])
        reg = sum(1 for r in records if r["regression"])
        avg = (sum(r["time_seconds"] for r in records) / total) if total else 0
        print(f"{agent:<10} {res}/{total:<10} {reg:<14} {avg:<12.1f}")
    print(sep)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="QuickSWE — benchmark coding agents on SWE tasks",
    )
    parser.add_argument(
        "--agent", choices=["amp", "amp-deep3", "claude", "both", "deep3-vs-claude"],
        default="both",
        help="Which agent(s) to run (default: both)",
    )
    parser.add_argument(
        "--tasks", default="all",
        help="Comma-separated task IDs or 'all' (default: all)",
    )
    parser.add_argument(
        "--timeout", type=int, default=300,
        help="Per-task timeout in seconds (default: 300)",
    )
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

    print(f"Tasks: {len(tasks)}  |  Agents: {', '.join(agents)}  |  Timeout: {args.timeout}s\n")

    all_records: dict[str, list[dict]] = {}

    for agent in agents:
        records = []
        for task_dir in tasks:
            print(f"[{agent}] Running {task_dir.name} ...", end=" ", flush=True)
            result = run_task(task_dir, agent, args.timeout)
            status = "RESOLVED" if result["resolved"] else "FAILED"
            if result.get("error"):
                status = f"ERROR ({result['error']})"
            print(status)
            records.append(result)

        result_path = save_results(agent, records)
        print(f"  -> Results saved: {result_path}")
        all_records[agent] = records

    print_summary(all_records)


if __name__ == "__main__":
    main()
