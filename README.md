# QuickSWE

**A fast, rigorous benchmark for evaluating AI coding agents on real-world Python tasks.**

QuickSWE runs on your laptop in hours — not days — with no Docker, no cloud infrastructure, and no terabytes of storage. Each of its 15 tasks is validated by real pytest suites, and built-in statistical multi-run aggregation delivers results you can trust. This is not a toy benchmark. It's a practical, repeatable measurement tool that tells you exactly how well your AI coding agent handles bug fixes, feature implementation, and code refactoring.

---

## Why QuickSWE?

|                        | **QuickSWE**                       | **SWE-Bench Verified**     | **SWE-Bench Pro**            |
|------------------------|-------------------------------------|----------------------------|------------------------------|
| **Tasks**              | 15 (curated, multi-category)       | 500                        | 731                          |
| **Languages**          | Python                             | Python                     | Python, Go, TS, JS           |
| **Requires Docker**    | No                                 | Yes                        | Yes                          |
| **Storage needed**     | < 100 MB                           | ~50 GB                     | ~200 GB                      |
| **Run time (1 pass)**  | ~1 hour                            | ~8 hours                   | ~24 hours                    |
| **Runs on laptop**     | ✅ Yes                              | ⚠️ Barely                   | ❌ No                         |
| **Task categories**    | Bug fix, Feature, Refactoring      | Bug fix only               | Mixed                        |
| **Statistical runs**   | Built-in (N runs + aggregation)    | Manual                     | Manual                       |
| **Visual dashboard**   | Built-in (10 interactive charts)   | No                         | No                           |
| **Measures regressions** | ✅ Yes                            | No                         | No                           |

QuickSWE is **not** a dumbed-down version of SWE-Bench. It's a fundamentally different design philosophy. Instead of 500 tasks you can barely run once on expensive hardware, QuickSWE gives you 15 carefully designed tasks you can run 5 times each with full statistical analysis. Multiple runs catch the non-deterministic behavior that single-pass benchmarks miss entirely — an agent that scores 80% on one run and 40% on the next isn't reliable, and you'd never know from a single pass. QuickSWE makes that visible.

---

## Quick Start

### One-click (Windows)

```powershell
# Quick test — 3 tasks, ~15 minutes
run_quick_test.bat

# Full benchmark — 15 tasks, 3 runs, ~4 hours
run_benchmark.bat
```

### Python

```powershell
pip install -r requirements.txt

# Run the benchmark (3 statistical runs, both agents)
python multi_runner.py --runs 3 --agent both

# Generate the interactive dashboard
python dashboard.py
```

---

## The 15 Tasks

| Task | Category | Difficulty | What It Tests |
|------|----------|------------|---------------|
| `task_001` | Bug Fix | Easy | Off-by-one error in paginator (0-indexed vs 1-indexed) |
| `task_002` | Bug Fix | Medium | CSV parser crash on empty input and trailing commas |
| `task_003` | Bug Fix | Easy | Wrong default encoding (ascii instead of utf-8) |
| `task_004` | Bug Fix | Medium | Email validation regex rejects valid addresses |
| `task_005` | Bug Fix | Hard | Shallow merge overwrites nested dicts instead of deep-merging |
| `task_006` | Feature | Easy | Add `sort_by(column, reverse)` to DataTable |
| `task_007` | Feature | Medium | Add retry with exponential backoff to HTTP client |
| `task_008` | Feature | Medium | Add JSON and file export to report generator |
| `task_009` | Feature | Easy | Add search and value calculation to inventory system |
| `task_010` | Feature | Hard | Add rate limiting (max N calls/sec) to API client |
| `task_011` | Refactoring | Easy | Extract duplicated validation into reusable functions |
| `task_012` | Refactoring | Easy | Replace magic numbers with named constants |
| `task_013` | Refactoring | Hard | Decompose god class into three focused components |
| `task_014` | Refactoring | Medium | Convert tuple-return error handling to exceptions |
| `task_015` | Refactoring | Medium | Flatten nested conditionals with early returns |

**Distribution:** 5 bug fixes · 5 features · 5 refactoring tasks — 4 easy · 6 medium · 3 hard

---

## What It Measures

- **Resolution Rate** — Did the agent fix the issue? Fail-to-pass tests must now pass.
- **Regression Safety** — Did the agent break anything? Pass-to-pass tests must still pass.
- **Speed** — Wall-clock time per task, per agent.
- **Consistency** — Does the agent produce the same result across N independent runs? Standard deviation and variance across runs reveal non-determinism.
- **Per-category breakdown** — Separate scores for bug fix, feature, and refactoring.
- **Per-difficulty breakdown** — Separate scores for easy, medium, and hard.

Every measurement is backed by real pytest execution. There is no LLM-as-judge, no subjective scoring, no vibes — tests pass or they don't.

---

## Dashboard

After a benchmark run, `python dashboard.py` generates an interactive HTML report that opens automatically in your browser. Ten chart types give you a complete picture:

| Chart | What It Shows |
|-------|---------------|
| 🏆 **Overall Resolution** | Head-to-head pass rate across all tasks |
| 📊 **Per-Task Heatmap** | Pass/fail matrix for every task × agent × run |
| 📈 **Category Breakdown** | Resolution rate by bug fix / feature / refactoring |
| ⏱️ **Timing Analysis** | Execution time distribution per agent |
| 🔄 **Consistency Radar** | Variance across multiple runs |
| 🛡️ **Regression Tracking** | Tests broken by agent changes |
| 📉 **Difficulty Curve** | Pass rate vs. task difficulty |
| 🔬 **Statistical Summary** | Mean, median, std dev, confidence intervals |
| 📋 **Detailed Results Table** | Sortable, filterable raw results |
| 🏅 **Agent Scorecard** | Final composite score per agent |

---

## Architecture

```
QuickSWE/
├── run_benchmark.bat        # Full benchmark (double-click to run)
├── run_quick_test.bat       # Quick smoke test (3 tasks)
├── multi_runner.py          # Statistical multi-run engine
├── runner.py                # Core task execution & agent invocation
├── dashboard.py             # Interactive HTML dashboard generator
├── report.py                # Console report with tables
├── requirements.txt         # Python dependencies
├── tasks/                   # 15 self-contained tasks
│   └── task_XXX/
│       ├── src/             # Source code with bug or missing feature
│       ├── tests/           # pytest suite (fail_to_pass + regression)
│       ├── description.md   # Issue description (given to the agent)
│       └── metadata.json    # Category, difficulty, task ID
└── results/                 # Auto-generated run results
```

Each task is fully self-contained. No external dependencies, no network access, no database. Copy a task directory to another machine and it works.

---

## Adding Your Own Agent

QuickSWE currently supports **Amp** and **Claude Code CLI**, but adding a new agent takes minutes:

1. Open `runner.py`
2. Find the `invoke_agent()` function
3. Add your agent's CLI command following the existing pattern:

```python
elif agent == "my_agent":
    cmd = ["my-agent-cli", "--task", task_description, "--workdir", task_dir]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
```

4. Run: `python multi_runner.py --runs 3 --agent my_agent`

---

## Adding Tasks

Create a new directory under `tasks/` following the existing structure:

```
tasks/task_016/
├── src/
│   └── module.py          # Code with the bug or missing feature
├── tests/
│   ├── test_fail_to_pass.py   # Tests that SHOULD fail before fix, pass after
│   └── test_regression.py     # Tests that MUST pass before and after
├── description.md             # What the agent sees as the "issue"
└── metadata.json              # {"id": "task_016", "category": "bug_fix", "difficulty": "medium", "description": "..."}
```

The runner auto-discovers all `task_*` directories. No registration needed.

---

## License

MIT

---

## Citation

```bibtex
@software{quickswe2026,
  title  = {QuickSWE: A Fast Benchmark for AI Coding Agents},
  author = {Daniel Zusmanovich},
  year   = {2026},
  url    = {https://github.com/zuwasi/QuickSWE}
}
```
