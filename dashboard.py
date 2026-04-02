"""Generate a comprehensive HTML dashboard from benchmark results.

Reads individual and aggregate JSON result files from results/ and produces
a self-contained HTML page with Chart.js visualisations.
"""

import argparse
import json
import os
import sys
import webbrowser
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

# ── data loading ─────────────────────────────────────────────────────────────

def load_individual_results(results_dir: Path) -> list[dict]:
    """Load all individual run result files."""
    files = sorted(results_dir.glob("*.json"))
    runs = []
    for f in files:
        if f.name.startswith("aggregate") or f.name == "dashboard.html":
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            if "results" in data and "agent" in data:
                runs.append(data)
        except (json.JSONDecodeError, KeyError):
            pass
    return runs


def load_aggregate(path: Path | None, results_dir: Path) -> dict | None:
    """Load aggregate file, or find the latest one."""
    if path and path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    aggs = sorted(results_dir.glob("aggregate_*.json"), reverse=True)
    if aggs:
        with open(aggs[0], encoding="utf-8") as f:
            return json.load(f)
    return None


# ── data aggregation ─────────────────────────────────────────────────────────

def aggregate_from_runs(runs: list[dict]) -> dict:
    """Build aggregate statistics from individual run files."""
    by_agent: dict[str, list[dict]] = defaultdict(list)
    for run in runs:
        agent = run["agent"]
        by_agent[agent].extend(run["results"])

    agents = sorted(by_agent.keys())
    task_ids = sorted({r["task_id"] for recs in by_agent.values() for r in recs})

    per_task: dict[str, dict] = {}
    for tid in task_ids:
        per_task[tid] = {}
        for agent in agents:
            recs = [r for r in by_agent[agent] if r["task_id"] == tid]
            if not recs:
                continue
            n = len(recs)
            resolved_count = sum(1 for r in recs if r["resolved"])
            regression_count = sum(1 for r in recs if r.get("regression"))
            times = [r["time_seconds"] for r in recs]
            per_task[tid][agent] = {
                "resolve_rate": resolved_count / n if n else 0,
                "regression_rate": regression_count / n if n else 0,
                "avg_time": sum(times) / n if n else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "runs": n,
                "category": recs[0].get("category", "unknown"),
                "difficulty": recs[0].get("difficulty", "unknown"),
            }

    # Per-run resolve counts (for trend chart)
    run_trends: dict[str, list[int]] = defaultdict(list)
    agent_runs: dict[str, list[list[dict]]] = defaultdict(list)
    for run in runs:
        agent = run["agent"]
        agent_runs[agent].append(run["results"])
    for agent in agents:
        for run_results in agent_runs[agent]:
            run_trends[agent].append(sum(1 for r in run_results if r["resolved"]))

    # Overall stats
    overall: dict[str, dict] = {}
    for agent in agents:
        recs = by_agent[agent]
        n = len(recs)
        overall[agent] = {
            "total": n,
            "resolved": sum(1 for r in recs if r["resolved"]),
            "regressions": sum(1 for r in recs if r.get("regression")),
            "avg_time": sum(r["time_seconds"] for r in recs) / n if n else 0,
            "resolve_rate": sum(1 for r in recs if r["resolved"]) / n if n else 0,
            "regression_rate": sum(1 for r in recs if r.get("regression")) / n if n else 0,
        }

    # By category
    by_category: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
    for agent in agents:
        cats = defaultdict(list)
        for r in by_agent[agent]:
            cats[r.get("category", "unknown")].append(r)
        for cat, recs in cats.items():
            n = len(recs)
            by_category[cat][agent] = {
                "resolve_rate": sum(1 for r in recs if r["resolved"]) / n if n else 0,
                "count": n,
            }

    # By difficulty
    by_difficulty: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
    for agent in agents:
        diffs = defaultdict(list)
        for r in by_agent[agent]:
            diffs[r.get("difficulty", "unknown")].append(r)
        for diff, recs in diffs.items():
            n = len(recs)
            by_difficulty[diff][agent] = {
                "resolve_rate": sum(1 for r in recs if r["resolved"]) / n if n else 0,
                "count": n,
            }

    num_runs = max((len(agent_runs[a]) for a in agents), default=0)

    return {
        "agents": agents,
        "task_ids": task_ids,
        "per_task": per_task,
        "overall": overall,
        "by_category": dict(by_category),
        "by_difficulty": dict(by_difficulty),
        "run_trends": dict(run_trends),
        "num_runs": num_runs,
        "num_tasks": len(task_ids),
    }


# ── HTML generation ──────────────────────────────────────────────────────────

def generate_html(agg: dict, output_path: Path):
    """Generate the full dashboard HTML."""
    agents = agg["agents"]
    a1 = agents[0] if agents else "amp"
    a2 = agents[1] if len(agents) > 1 else "claude"

    # Determine winner
    r1 = agg["overall"].get(a1, {}).get("resolve_rate", 0)
    r2 = agg["overall"].get(a2, {}).get("resolve_rate", 0)
    if r1 > r2:
        winner = a1
    elif r2 > r1:
        winner = a2
    else:
        winner = "Tie"

    # Prepare chart data as JSON strings
    chart_data = build_chart_data(agg, a1, a2)

    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        num_tasks=agg["num_tasks"],
        num_runs=agg["num_runs"],
        agent1=a1.capitalize(),
        agent2=a2.capitalize(),
        winner=winner.capitalize(),
        a1_resolve=f"{r1*100:.1f}",
        a2_resolve=f"{r2*100:.1f}",
        a1_color="#00B4D8",
        a2_color="#FF6B35",
        **chart_data,
    )

    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def build_chart_data(agg: dict, a1: str, a2: str) -> dict:
    """Build all chart data as JSON strings for template insertion."""
    overall = agg["overall"]
    per_task = agg["per_task"]
    task_ids = agg["task_ids"]
    by_cat = agg["by_category"]
    by_diff = agg["by_difficulty"]
    trends = agg["run_trends"]

    # 1. Overall resolve rates
    overall_data = json.dumps({
        "labels": [a1.capitalize(), a2.capitalize()],
        "a1": round(overall.get(a1, {}).get("resolve_rate", 0) * 100, 1),
        "a2": round(overall.get(a2, {}).get("resolve_rate", 0) * 100, 1),
    })

    # 2. By category
    categories = sorted(by_cat.keys())
    cat_data = json.dumps({
        "labels": [c.replace("_", " ").title() for c in categories],
        "a1": [round(by_cat[c].get(a1, {}).get("resolve_rate", 0) * 100, 1) for c in categories],
        "a2": [round(by_cat[c].get(a2, {}).get("resolve_rate", 0) * 100, 1) for c in categories],
    })

    # 3. By difficulty
    diff_order = ["easy", "medium", "hard"]
    diffs = [d for d in diff_order if d in by_diff]
    diff_data = json.dumps({
        "labels": [d.title() for d in diffs],
        "a1": [round(by_diff[d].get(a1, {}).get("resolve_rate", 0) * 100, 1) for d in diffs],
        "a2": [round(by_diff[d].get(a2, {}).get("resolve_rate", 0) * 100, 1) for d in diffs],
    })

    # 4. Per-task comparison (sorted by biggest difference)
    task_pairs = []
    for tid in task_ids:
        r1 = per_task.get(tid, {}).get(a1, {}).get("resolve_rate", 0)
        r2 = per_task.get(tid, {}).get(a2, {}).get("resolve_rate", 0)
        task_pairs.append((tid, r1, r2, abs(r1 - r2)))
    task_pairs.sort(key=lambda x: -x[3])
    per_task_data = json.dumps({
        "labels": [t[0] for t in task_pairs],
        "a1": [round(t[1] * 100, 1) for t in task_pairs],
        "a2": [round(t[2] * 100, 1) for t in task_pairs],
    })

    # 5. Time comparison
    time_data = json.dumps({
        "labels": [tid for tid in task_ids],
        "a1": [round(per_task.get(tid, {}).get(a1, {}).get("avg_time", 0), 1) for tid in task_ids],
        "a2": [round(per_task.get(tid, {}).get(a2, {}).get("avg_time", 0), 1) for tid in task_ids],
    })

    # 6. Trend data
    trend_data = json.dumps({
        "a1": trends.get(a1, []),
        "a2": trends.get(a2, []),
    })

    # 7. Outcome pie data
    def outcome_counts(agent):
        recs_total = overall.get(agent, {}).get("total", 0)
        resolved = overall.get(agent, {}).get("resolved", 0)
        regressions = overall.get(agent, {}).get("regressions", 0)
        resolved_clean = resolved - min(regressions, resolved)
        failed = recs_total - resolved
        return {"resolved": resolved_clean, "regression": regressions, "failed": failed}

    pie_data = json.dumps({
        "a1": outcome_counts(a1),
        "a2": outcome_counts(a2),
    })

    # 8. Regression rate
    reg_data = json.dumps({
        "labels": [a1.capitalize(), a2.capitalize()],
        "a1": round(overall.get(a1, {}).get("regression_rate", 0) * 100, 1),
        "a2": round(overall.get(a2, {}).get("regression_rate", 0) * 100, 1),
    })

    # 9. Heatmap table rows
    heatmap_rows = ""
    for tid in task_ids:
        t1 = per_task.get(tid, {}).get(a1, {})
        t2 = per_task.get(tid, {}).get(a2, {})
        cat = t1.get("category", t2.get("category", ""))
        r1 = t1.get("resolve_rate", 0)
        r2 = t2.get("resolve_rate", 0)
        rg1 = t1.get("regression_rate", 0)
        rg2 = t2.get("regression_rate", 0)
        tm1 = t1.get("avg_time", 0)
        tm2 = t2.get("avg_time", 0)

        def cell_class(resolve, regress):
            if resolve >= 0.8 and regress < 0.2:
                return "cell-pass"
            elif resolve >= 0.5:
                return "cell-partial"
            elif resolve > 0:
                return "cell-warn"
            return "cell-fail"

        c1 = cell_class(r1, rg1)
        c2 = cell_class(r2, rg2)
        heatmap_rows += (
            f'<tr><td>{tid}</td><td>{cat.replace("_"," ").title()}</td>'
            f'<td class="{c1}">{r1*100:.0f}%</td><td>{tm1:.1f}s</td>'
            f'<td class="{c2}">{r2*100:.0f}%</td><td>{tm2:.1f}s</td></tr>\n'
        )

    # 10. Radar data
    def safe_rate(agent, key, src):
        return round(src.get(agent, {}).get(key, 0) * 100, 1)

    max_time = max(
        overall.get(a1, {}).get("avg_time", 1),
        overall.get(a2, {}).get("avg_time", 1),
        1,
    )
    speed1 = round((1 - overall.get(a1, {}).get("avg_time", 0) / max_time) * 100, 1) if max_time else 0
    speed2 = round((1 - overall.get(a2, {}).get("avg_time", 0) / max_time) * 100, 1) if max_time else 0
    noreg1 = round((1 - overall.get(a1, {}).get("regression_rate", 0)) * 100, 1)
    noreg2 = round((1 - overall.get(a2, {}).get("regression_rate", 0)) * 100, 1)

    # Consistency: lower std across runs = more consistent
    def consistency_score(agent_trends):
        if len(agent_trends) < 2:
            return 100.0
        mean = sum(agent_trends) / len(agent_trends)
        var = sum((x - mean) ** 2 for x in agent_trends) / len(agent_trends)
        std = var ** 0.5
        max_val = max(agent_trends) if agent_trends else 1
        return round(max(0, (1 - std / max(max_val, 1)) * 100), 1)

    cons1 = consistency_score(trends.get(a1, []))
    cons2 = consistency_score(trends.get(a2, []))

    radar_data = json.dumps({
        "labels": ["Resolve Rate", "Speed", "Consistency", "No Regressions",
                    "Bug Fix", "Feature", "Refactoring"],
        "a1": [
            safe_rate(a1, "resolve_rate", overall),
            speed1, cons1, noreg1,
            round(by_cat.get("bug_fix", {}).get(a1, {}).get("resolve_rate", 0) * 100, 1),
            round(by_cat.get("feature", {}).get(a1, {}).get("resolve_rate", 0) * 100, 1),
            round(by_cat.get("refactoring", {}).get(a1, {}).get("resolve_rate", 0) * 100, 1),
        ],
        "a2": [
            safe_rate(a2, "resolve_rate", overall),
            speed2, cons2, noreg2,
            round(by_cat.get("bug_fix", {}).get(a2, {}).get("resolve_rate", 0) * 100, 1),
            round(by_cat.get("feature", {}).get(a2, {}).get("resolve_rate", 0) * 100, 1),
            round(by_cat.get("refactoring", {}).get(a2, {}).get("resolve_rate", 0) * 100, 1),
        ],
    })

    return {
        "overall_data": overall_data,
        "category_data": cat_data,
        "difficulty_data": diff_data,
        "per_task_data": per_task_data,
        "time_data": time_data,
        "trend_data": trend_data,
        "pie_data": pie_data,
        "regression_data": reg_data,
        "heatmap_rows": heatmap_rows,
        "radar_data": radar_data,
    }


# ── HTML template ────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QuickSWE Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
<style>
  :root {{
    --bg: #1a1a2e; --card: #16213e; --card-border: #0f3460;
    --text: #e0e0e0; --muted: #8899aa; --accent1: {a1_color}; --accent2: {a2_color};
    --pass: #2ecc71; --warn: #f39c12; --fail: #e74c3c; --partial: #3498db; --gray: #555;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',system-ui,sans-serif; padding:24px; }}
  h1 {{ font-size:2rem; margin-bottom:4px; }}
  .subtitle {{ color:var(--muted); margin-bottom:20px; font-size:.9rem; }}
  .summary-cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:28px; }}
  .scard {{ background:var(--card); border:1px solid var(--card-border); border-radius:10px; padding:18px; text-align:center; }}
  .scard .val {{ font-size:1.8rem; font-weight:700; }}
  .scard .lbl {{ color:var(--muted); font-size:.8rem; margin-top:4px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(500px,1fr)); gap:20px; margin-bottom:24px; }}
  .card {{ background:var(--card); border:1px solid var(--card-border); border-radius:12px; padding:22px; }}
  .card h2 {{ font-size:1.15rem; margin-bottom:6px; }}
  .card .explain {{ color:var(--muted); font-size:.82rem; margin-top:10px; line-height:1.45; }}
  .card canvas {{ max-height:340px; }}
  .full {{ grid-column:1/-1; }}
  table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
  th, td {{ padding:8px 10px; text-align:center; border-bottom:1px solid var(--card-border); }}
  th {{ color:var(--muted); font-weight:600; }}
  .cell-pass {{ background:#1a4d2e; color:#2ecc71; font-weight:700; }}
  .cell-partial {{ background:#1a3a5c; color:#3498db; }}
  .cell-warn {{ background:#4d3a1a; color:#f39c12; }}
  .cell-fail {{ background:#4d1a1a; color:#e74c3c; }}
  footer {{ text-align:center; color:var(--muted); font-size:.8rem; margin-top:30px; }}
  .achievement {{ background: linear-gradient(135deg, #1a3a1a 0%, #16213e 100%); border:2px solid #2ecc71; border-radius:14px; padding:28px; margin-bottom:24px; }}
  .achievement h2 {{ color:#2ecc71; font-size:1.3rem; margin-bottom:12px; }}
  .achievement .highlight {{ color:#f1c40f; font-weight:700; }}
  .achievement p {{ line-height:1.6; margin-bottom:10px; }}
  .achievement .detail-box {{ background:#0d1a0d; border:1px solid #2ecc7744; border-radius:8px; padding:16px; margin-top:14px; font-size:.9rem; }}
  .achievement .detail-box code {{ background:#1a2e1a; padding:2px 6px; border-radius:4px; color:#2ecc71; }}
  .achievement .vs-table {{ width:100%; margin-top:14px; }}
  .achievement .vs-table td {{ padding:8px 12px; text-align:center; }}
  .achievement .vs-table .amp-col {{ background:#1a3a1a; color:#2ecc71; font-weight:700; border-radius:6px; }}
  .achievement .vs-col {{ background:#3a1a1a; color:#e74c3c; border-radius:6px; }}
</style>
</head>
<body>

<h1>QuickSWE Dashboard</h1>
<p class="subtitle">Generated {timestamp} &nbsp;|&nbsp; {num_tasks} tasks &nbsp;|&nbsp; {num_runs} run(s) per agent</p>

<div class="summary-cards">
  <div class="scard"><div class="val">{num_tasks}</div><div class="lbl">Tasks</div></div>
  <div class="scard"><div class="val">{num_runs}</div><div class="lbl">Runs / Agent</div></div>
  <div class="scard"><div class="val" style="color:var(--accent1)">{a1_resolve}%</div><div class="lbl">{agent1} Resolve Rate</div></div>
  <div class="scard"><div class="val" style="color:var(--accent2)">{a2_resolve}%</div><div class="lbl">{agent2} Resolve Rate</div></div>
  <div class="scard"><div class="val" style="color:var(--pass)">🏆 {winner}</div><div class="lbl">Overall Winner</div></div>
</div>

<div class="achievement">
  <h2>&#127942; Notable Finding: Amp Catches a Bug in the Benchmark Itself</h2>
  <p>During testing of <strong>task_032</strong> (SQL Query Engine), <span class="highlight">Amp identified and refused to comply with an incorrect test assertion</span>. The test expected <code>len(result) == 2</code> for a <code>WHERE amount > 200</code> query against orders with amounts [250, 150, 300, 450, 200]. The mathematically correct answer is <strong>3</strong> (amounts 250, 300, and 450 all satisfy <code>&gt; 200</code>).</p>
  <p>Instead of blindly producing code to pass the wrong test, Amp analyzed the data, performed the arithmetic, and <span class="highlight">correctly flagged the discrepancy</span> in its output &mdash; consistently across all 3 runs.</p>
  <div class="detail-box">
    <strong>What each agent did:</strong>
    <table class="vs-table">
      <tr>
        <td style="color:var(--muted)">Agent</td>
        <td style="color:var(--muted)">Behavior on incorrect test</td>
        <td style="color:var(--muted)">Result</td>
      </tr>
      <tr>
        <td style="color:var(--accent1)"><strong>Amp</strong></td>
        <td class="amp-col">Analyzed the data, identified the assertion was wrong (expected 2, correct answer is 3), and refused to produce incorrect code</td>
        <td class="amp-col">0% pass &mdash; correctly rejected bad test</td>
      </tr>
      <tr>
        <td style="color:var(--accent2)"><strong>Claude Code</strong></td>
        <td class="vs-col">Brute-forced a solution that sometimes matched the wrong assertion by coincidence</td>
        <td class="vs-col">67% pass &mdash; passed a test that was wrong</td>
      </tr>
    </table>
    <p style="margin-top:12px;color:#aaa;"><strong>Verdict:</strong> A higher pass rate on a flawed test is not a win &mdash; it means the agent lacks the reasoning to question incorrect specifications. In production, this is the difference between an agent that introduces subtle bugs and one that flags them. <span class="highlight">Reasoning integrity &gt; blind compliance.</span></p>
  </div>
</div>

<div class="grid">

<!-- 1. Overall Resolution -->
<div class="card">
  <h2>📊 Overall Resolution Rate</h2>
  <canvas id="overallChart"></canvas>
  <p class="explain">Percentage of tasks each agent successfully resolved across all runs. Higher is better.</p>
</div>

<!-- 2. By Category -->
<div class="card">
  <h2>📂 Resolution by Category</h2>
  <canvas id="categoryChart"></canvas>
  <p class="explain">How each agent performs across bug fixes, features, and refactoring tasks. Reveals strengths per task type.</p>
</div>

<!-- 3. By Difficulty -->
<div class="card">
  <h2>📈 Resolution by Difficulty</h2>
  <canvas id="difficultyChart"></canvas>
  <p class="explain">Performance scaling with task difficulty. Steeper drops indicate the agent struggles with complexity.</p>
</div>

<!-- 4. Regression Rate -->
<div class="card">
  <h2>🛡️ Regression Rate</h2>
  <canvas id="regressionChart"></canvas>
  <p class="explain">Percentage of tasks where the agent broke existing tests while fixing the issue. Lower is better.</p>
</div>

<!-- 7. Pie Charts -->
<div class="card">
  <h2>🥧 {agent1} — Outcome Breakdown</h2>
  <canvas id="pie1"></canvas>
  <p class="explain">Distribution of outcomes: resolved cleanly, resolved with regressions, or failed.</p>
</div>
<div class="card">
  <h2>🥧 {agent2} — Outcome Breakdown</h2>
  <canvas id="pie2"></canvas>
  <p class="explain">Distribution of outcomes: resolved cleanly, resolved with regressions, or failed.</p>
</div>

<!-- 10. Radar -->
<div class="card full">
  <h2>🕸️ Multi-Dimensional Comparison</h2>
  <canvas id="radarChart" style="max-height:420px;"></canvas>
  <p class="explain">Spider chart comparing agents across resolve rate, speed, consistency, regression safety, and per-category performance. Larger area = stronger overall agent.</p>
</div>

<!-- 5. Time Comparison -->
<div class="card full">
  <h2>⏱️ Average Time per Task</h2>
  <canvas id="timeChart" style="max-height:300px;"></canvas>
  <p class="explain">Average seconds each agent spent per task. Shorter bars indicate faster performance.</p>
</div>

<!-- 6. Consistency / Trend -->
<div class="card full">
  <h2>📉 Consistency Across Runs</h2>
  <canvas id="trendChart" style="max-height:280px;"></canvas>
  <p class="explain">Number of tasks resolved in each successive run. Flat lines indicate high reliability; erratic lines suggest non-deterministic behavior.</p>
</div>

<!-- 4. Per-Task Comparison -->
<div class="card full">
  <h2>🔍 Per-Task Comparison</h2>
  <canvas id="perTaskChart" style="max-height:500px;"></canvas>
  <p class="explain">Task-level resolve rates sorted by biggest performance gap. Shows where each agent uniquely excels or struggles.</p>
</div>

<!-- 9. Heatmap Table -->
<div class="card full">
  <h2>🗺️ Head-to-Head Results Matrix</h2>
  <div style="overflow-x:auto;">
  <table>
    <thead><tr>
      <th>Task</th><th>Category</th>
      <th style="color:var(--accent1)">{agent1} Resolve</th><th style="color:var(--accent1)">Time</th>
      <th style="color:var(--accent2)">{agent2} Resolve</th><th style="color:var(--accent2)">Time</th>
    </tr></thead>
    <tbody>{heatmap_rows}</tbody>
  </table>
  </div>
  <p class="explain">Green = ≥80% resolved with &lt;20% regressions. Blue = ≥50%. Yellow = partial. Red = not resolved.</p>
</div>

</div>

<footer>Generated by <strong>QuickSWE</strong> &nbsp;|&nbsp; {timestamp}</footer>

<script>
Chart.register(ChartDataLabels);
const A1 = '{a1_color}', A2 = '{a2_color}';
const A1a = '{a1_color}88', A2a = '{a2_color}88';
const FONT = {{ color: '#e0e0e0' }};
const GRID = {{ color: '#ffffff15' }};
function darkOpts(o) {{
  o.plugins = o.plugins || {{}};
  o.plugins.legend = o.plugins.legend || {{}};
  o.plugins.legend.labels = {{ ...o.plugins.legend.labels, color:'#e0e0e0' }};
  if (o.scales) {{
    for (let k in o.scales) {{
      o.scales[k].ticks = {{ ...o.scales[k].ticks, color:'#aaa' }};
      o.scales[k].grid = {{ ...o.scales[k].grid, color:'#ffffff10' }};
    }}
  }}
  return o;
}}

// 1. Overall
(function(){{
  const d = {overall_data};
  new Chart('overallChart', darkOpts({{
    type:'bar', data:{{
      labels:d.labels,
      datasets:[{{ data:[d.a1,d.a2], backgroundColor:[A1,A2], borderRadius:6 }}]
    }}, options:{{ indexAxis:'y', plugins:{{ legend:{{display:false}}, datalabels:{{ anchor:'end',align:'left',color:'#fff',font:{{weight:'bold',size:16}},formatter:v=>v+'%' }} }},
      scales:{{ x:{{ max:100, title:{{display:true,text:'Resolve Rate %',color:'#aaa'}} }} }}
    }}
  }}));
}})();

// 2. Category
(function(){{
  const d = {category_data};
  new Chart('categoryChart', darkOpts({{
    type:'bar', data:{{
      labels:d.labels,
      datasets:[
        {{ label:'{agent1}', data:d.a1, backgroundColor:A1, borderRadius:4 }},
        {{ label:'{agent2}', data:d.a2, backgroundColor:A2, borderRadius:4 }}
      ]
    }}, options:{{ plugins:{{ datalabels:{{ color:'#fff',font:{{size:11}},formatter:v=>v+'%' }} }},
      scales:{{ y:{{ max:100, title:{{display:true,text:'%',color:'#aaa'}} }} }}
    }}
  }}));
}})();

// 3. Difficulty
(function(){{
  const d = {difficulty_data};
  new Chart('difficultyChart', darkOpts({{
    type:'bar', data:{{
      labels:d.labels,
      datasets:[
        {{ label:'{agent1}', data:d.a1, backgroundColor:A1, borderRadius:4 }},
        {{ label:'{agent2}', data:d.a2, backgroundColor:A2, borderRadius:4 }}
      ]
    }}, options:{{ plugins:{{ datalabels:{{ color:'#fff',font:{{size:11}},formatter:v=>v+'%' }} }},
      scales:{{ y:{{ max:100 }} }}
    }}
  }}));
}})();

// 4. Regression
(function(){{
  const d = {regression_data};
  new Chart('regressionChart', darkOpts({{
    type:'bar', data:{{
      labels:d.labels,
      datasets:[{{ data:[d.a1,d.a2], backgroundColor:[A1,A2], borderRadius:6 }}]
    }}, options:{{ plugins:{{ legend:{{display:false}}, datalabels:{{ color:'#fff',font:{{weight:'bold',size:14}},formatter:v=>v+'%' }} }},
      scales:{{ y:{{ title:{{display:true,text:'Regression %',color:'#aaa'}} }} }}
    }}
  }}));
}})();

// 5. Pie charts
(function(){{
  const d = {pie_data};
  const colors = ['#2ecc71','#f39c12','#e74c3c'];
  const labels = ['Resolved','Regression','Failed'];
  new Chart('pie1', {{ type:'doughnut', data:{{
    labels, datasets:[{{ data:[d.a1.resolved,d.a1.regression,d.a1.failed], backgroundColor:colors }}]
  }}, options:{{ plugins:{{ legend:{{labels:{{color:'#ccc'}}}}, datalabels:{{ color:'#fff', font:{{weight:'bold'}}, formatter:(v,ctx)=>v?ctx.chart.data.labels[ctx.dataIndex]+': '+v:'' }} }} }} }});
  new Chart('pie2', {{ type:'doughnut', data:{{
    labels, datasets:[{{ data:[d.a2.resolved,d.a2.regression,d.a2.failed], backgroundColor:colors }}]
  }}, options:{{ plugins:{{ legend:{{labels:{{color:'#ccc'}}}}, datalabels:{{ color:'#fff', font:{{weight:'bold'}}, formatter:(v,ctx)=>v?ctx.chart.data.labels[ctx.dataIndex]+': '+v:'' }} }} }} }});
}})();

// 6. Radar
(function(){{
  const d = {radar_data};
  new Chart('radarChart', darkOpts({{
    type:'radar', data:{{
      labels:d.labels,
      datasets:[
        {{ label:'{agent1}', data:d.a1, borderColor:A1, backgroundColor:A1a, pointBackgroundColor:A1 }},
        {{ label:'{agent2}', data:d.a2, borderColor:A2, backgroundColor:A2a, pointBackgroundColor:A2 }}
      ]
    }}, options:{{ scales:{{ r:{{ min:0, max:100, ticks:{{color:'#888',backdropColor:'transparent'}}, grid:{{color:'#ffffff15'}}, pointLabels:{{color:'#ccc',font:{{size:12}}}} }} }},
      plugins:{{ datalabels:{{display:false}} }}
    }}
  }}));
}})();

// 7. Time
(function(){{
  const d = {time_data};
  new Chart('timeChart', darkOpts({{
    type:'bar', data:{{
      labels:d.labels,
      datasets:[
        {{ label:'{agent1}', data:d.a1, backgroundColor:A1, borderRadius:3 }},
        {{ label:'{agent2}', data:d.a2, backgroundColor:A2, borderRadius:3 }}
      ]
    }}, options:{{ plugins:{{ datalabels:{{ display:false }} }},
      scales:{{ y:{{ title:{{display:true,text:'Seconds',color:'#aaa'}} }} }}
    }}
  }}));
}})();

// 8. Trend
(function(){{
  const d = {trend_data};
  const maxLen = Math.max(d.a1.length, d.a2.length);
  const labels = Array.from({{length:maxLen}}, (_,i)=>'Run '+(i+1));
  new Chart('trendChart', darkOpts({{
    type:'line', data:{{
      labels,
      datasets:[
        {{ label:'{agent1}', data:d.a1, borderColor:A1, backgroundColor:A1a, tension:.3, fill:false, pointRadius:5 }},
        {{ label:'{agent2}', data:d.a2, borderColor:A2, backgroundColor:A2a, tension:.3, fill:false, pointRadius:5 }}
      ]
    }}, options:{{ plugins:{{ datalabels:{{ color:'#fff', anchor:'end', align:'top', font:{{size:11}} }} }},
      scales:{{ y:{{ title:{{display:true,text:'Tasks Resolved',color:'#aaa'}}, beginAtZero:true }} }}
    }}
  }}));
}})();

// 9. Per-task
(function(){{
  const d = {per_task_data};
  new Chart('perTaskChart', darkOpts({{
    type:'bar', data:{{
      labels:d.labels,
      datasets:[
        {{ label:'{agent1}', data:d.a1, backgroundColor:A1, borderRadius:3 }},
        {{ label:'{agent2}', data:d.a2, backgroundColor:A2, borderRadius:3 }}
      ]
    }}, options:{{ indexAxis:'y', plugins:{{ datalabels:{{ display:false }} }},
      scales:{{ x:{{ max:100, title:{{display:true,text:'Resolve Rate %',color:'#aaa'}} }} }}
    }}
  }}));
}})();
</script>
</body>
</html>"""


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate benchmark dashboard")
    parser.add_argument("--output", type=Path, default=RESULTS_DIR / "dashboard.html")
    parser.add_argument("--aggregate", type=Path, default=None)
    parser.add_argument("--no-open", action="store_true", help="Don't open in browser")
    args = parser.parse_args()

    # Always build from individual run files for consistent structure
    runs = load_individual_results(RESULTS_DIR)
    if not runs:
        print("ERROR: No result files found in", RESULTS_DIR)
        sys.exit(1)
    print(f"Building aggregate from {len(runs)} individual run file(s)...")
    agg = aggregate_from_runs(runs)

    generate_html(agg, args.output)
    print(f"Dashboard generated: {args.output}")

    if not args.no_open:
        webbrowser.open(str(args.output.resolve()))


if __name__ == "__main__":
    main()
