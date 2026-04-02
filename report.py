"""Report generator: reads benchmark result JSON files and produces comparisons."""

import argparse
import html as html_mod
import json
import sys
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


# ── data loading ─────────────────────────────────────────────────────────────

def load_result_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_results() -> list[dict]:
    """Load every JSON result file in the results directory."""
    if not RESULTS_DIR.is_dir():
        print(f"No results directory found: {RESULTS_DIR}")
        sys.exit(1)

    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        print("No result files found.")
        sys.exit(1)

    data = []
    for f in files:
        try:
            data.append(load_result_file(f))
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"WARNING: skipping {f.name}: {exc}")
    return data


def latest_per_agent(datasets: list[dict]) -> dict[str, list[dict]]:
    """Keep only the most recent run per agent."""
    latest: dict[str, dict] = {}
    for ds in datasets:
        agent = ds["agent"]
        ts = ds.get("timestamp", "")
        if agent not in latest or ts > latest[agent]["timestamp"]:
            latest[agent] = ds
    return {a: d["results"] for a, d in latest.items()}


# ── stats helpers ────────────────────────────────────────────────────────────

def agent_summary(records: list[dict]) -> dict:
    total = len(records)
    resolved = sum(1 for r in records if r["resolved"])
    regressions = sum(1 for r in records if r["regression"])
    times = [r["time_seconds"] for r in records if r["time_seconds"] > 0]
    avg_time = (sum(times) / len(times)) if times else 0
    return {
        "total": total,
        "resolved": resolved,
        "regressions": regressions,
        "avg_time": round(avg_time, 1),
        "resolve_rate": round(resolved / total * 100, 1) if total else 0,
    }


def by_category(records: list[dict]) -> dict[str, dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[r.get("category", "unknown")].append(r)
    return {cat: agent_summary(recs) for cat, recs in sorted(groups.items())}


# ── ASCII table output ──────────────────────────────────────────────────────

def print_table(agent_data: dict[str, list[dict]]):
    sep = "=" * 85

    # ── per-task comparison ──
    print(f"\n{sep}")
    print("PER-TASK RESULTS")
    print(sep)

    all_task_ids = sorted({r["task_id"] for recs in agent_data.values() for r in recs})
    agents = sorted(agent_data)

    header = f"{'Task':<20}"
    for a in agents:
        header += f" | {a+' Res':<10} {a+' Time':<10} {a+' Reg':<8}"
    print(header)
    print("-" * len(header))

    for tid in all_task_ids:
        row = f"{tid:<20}"
        for a in agents:
            rec = next((r for r in agent_data[a] if r["task_id"] == tid), None)
            if rec:
                res = "YES" if rec["resolved"] else "NO"
                t = f"{rec['time_seconds']:.1f}s"
                reg = "YES" if rec["regression"] else "-"
            else:
                res, t, reg = "N/A", "-", "-"
            row += f" | {res:<10} {t:<10} {reg:<8}"
        print(row)

    # ── summary ──
    print(f"\n{sep}")
    print("SUMMARY")
    print(sep)
    print(f"{'Agent':<10} {'Resolved':<14} {'Rate':<8} {'Regressions':<14} {'Avg Time':<10}")
    print("-" * 56)
    for a in agents:
        s = agent_summary(agent_data[a])
        print(
            f"{a:<10} {s['resolved']}/{s['total']:<12} "
            f"{s['resolve_rate']}%{'':<3} {s['regressions']:<14} {s['avg_time']}s"
        )

    # ── by category ──
    print(f"\n{sep}")
    print("BY CATEGORY")
    print(sep)
    print(f"{'Category':<16} ", end="")
    for a in agents:
        print(f"| {a+' Rate':<14} ", end="")
    print()
    print("-" * (18 + 17 * len(agents)))

    all_cats = sorted({
        r.get("category", "unknown")
        for recs in agent_data.values() for r in recs
    })
    for cat in all_cats:
        print(f"{cat:<16} ", end="")
        for a in agents:
            cats = by_category(agent_data[a])
            if cat in cats:
                c = cats[cat]
                print(f"| {c['resolved']}/{c['total']} ({c['resolve_rate']}%){'':<2} ", end="")
            else:
                print(f"| {'N/A':<14} ", end="")
        print()

    print(sep)


# ── HTML output ──────────────────────────────────────────────────────────────

def generate_html(agent_data: dict[str, list[dict]], out_path: Path):
    agents = sorted(agent_data)
    all_task_ids = sorted({r["task_id"] for recs in agent_data.values() for r in recs})

    def e(text):
        return html_mod.escape(str(text))

    lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        "<title>Amp vs Claude Benchmark Report</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;margin:2em;background:#f8f9fa}",
        "h1{color:#1a1a2e} h2{margin-top:2em;color:#16213e}",
        "table{border-collapse:collapse;width:100%;margin:1em 0}",
        "th,td{border:1px solid #ccc;padding:8px 12px;text-align:left}",
        "th{background:#e2e8f0} tr:nth-child(even){background:#f1f5f9}",
        ".yes{color:#16a34a;font-weight:bold} .no{color:#dc2626;font-weight:bold}",
        "</style></head><body>",
        "<h1>Amp vs Claude Code — Benchmark Report</h1>",
    ]

    # Per-task table
    lines.append("<h2>Per-Task Results</h2><table><tr><th>Task</th>")
    for a in agents:
        lines.append(f"<th>{e(a)} Resolved</th><th>{e(a)} Time</th><th>{e(a)} Regression</th>")
    lines.append("</tr>")

    for tid in all_task_ids:
        lines.append(f"<tr><td>{e(tid)}</td>")
        for a in agents:
            rec = next((r for r in agent_data[a] if r["task_id"] == tid), None)
            if rec:
                rc = "yes" if rec["resolved"] else "no"
                lines.append(f"<td class='{rc}'>{'YES' if rec['resolved'] else 'NO'}</td>")
                lines.append(f"<td>{rec['time_seconds']:.1f}s</td>")
                rg = "yes" if rec["regression"] else "no"
                rg_label = "YES" if rec["regression"] else "-"
                lines.append(f"<td class='{rg if rec['regression'] else ''}'>{rg_label}</td>")
            else:
                lines.append("<td>N/A</td><td>-</td><td>-</td>")
        lines.append("</tr>")
    lines.append("</table>")

    # Summary
    lines.append("<h2>Summary</h2><table>")
    lines.append("<tr><th>Agent</th><th>Resolved</th><th>Rate</th>"
                 "<th>Regressions</th><th>Avg Time</th></tr>")
    for a in agents:
        s = agent_summary(agent_data[a])
        lines.append(
            f"<tr><td>{e(a)}</td><td>{s['resolved']}/{s['total']}</td>"
            f"<td>{s['resolve_rate']}%</td><td>{s['regressions']}</td>"
            f"<td>{s['avg_time']}s</td></tr>"
        )
    lines.append("</table>")

    # By category
    lines.append("<h2>By Category</h2><table><tr><th>Category</th>")
    for a in agents:
        lines.append(f"<th>{e(a)} Rate</th>")
    lines.append("</tr>")
    all_cats = sorted({
        r.get("category", "unknown")
        for recs in agent_data.values() for r in recs
    })
    for cat in all_cats:
        lines.append(f"<tr><td>{e(cat)}</td>")
        for a in agents:
            cats = by_category(agent_data[a])
            if cat in cats:
                c = cats[cat]
                lines.append(f"<td>{c['resolved']}/{c['total']} ({c['resolve_rate']}%)</td>")
            else:
                lines.append("<td>N/A</td>")
        lines.append("</tr>")
    lines.append("</table>")

    lines.append("</body></html>")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"HTML report written to {out_path}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Benchmark report generator")
    parser.add_argument(
        "--format", choices=["table", "html"], default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--compare", nargs=2, metavar="FILE",
        help="Compare two specific result JSON files",
    )
    args = parser.parse_args()

    if args.compare:
        datasets = [load_result_file(Path(p)) for p in args.compare]
        agent_data = {ds["agent"]: ds["results"] for ds in datasets}
    else:
        datasets = load_all_results()
        agent_data = latest_per_agent(datasets)

    if not agent_data:
        print("No data to report.")
        sys.exit(1)

    if args.format == "table":
        print_table(agent_data)
    else:
        out = Path(__file__).parent / "report.html"
        generate_html(agent_data, out)


if __name__ == "__main__":
    main()
