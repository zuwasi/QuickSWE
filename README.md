# QuickSWE v2

**A fast, rigorous benchmark for evaluating AI coding agents across Python, C++, and CUDA.**

QuickSWE v2 features **100 stress-test tasks** across three languages and four difficulty tiers, designed to push frontier AI coding agents to their limits. The v1 benchmark had 100% solve rates on Python and C++ — v2 fixes that with genuinely hard tasks requiring deep algorithmic reasoning.

---

## What's New in v2

- **100 tasks** (up from 85): 50 Python · 25 C++ · 25 CUDA
- **Much harder tasks**: Red-black trees, compilers, VMs, GCs, type inference, CUDA dynamic parallelism, lock-free data structures
- **Amp Deep³ vs Claude Code**: Head-to-head comparison using Amp's maximum reasoning mode (`xhigh`)
- **Clickable dashboard**: Task bars and heatmap rows link directly to source code on GitHub
- **Difficulty badges**: 🟢 Easy · 🟡 Medium · 🟠 Hard · 🔴 Extreme

---

## Why QuickSWE?

|                        | **QuickSWE v2**                    | **SWE-Bench Verified**     | **SWE-Bench Pro**            |
|------------------------|-------------------------------------|----------------------------|------------------------------|
| **Tasks**              | 100 (curated, multi-language)      | 500                        | 731                          |
| **Languages**          | Python, C++, CUDA                  | Python                     | Python, Go, TS, JS           |
| **Requires Docker**    | No                                 | Yes                        | Yes                          |
| **Storage needed**     | < 100 MB                           | ~50 GB                     | ~200 GB                      |
| **Runs on laptop**     | ✅ Yes                              | ⚠️ Barely                   | ❌ No                         |
| **Task categories**    | Bug fix, Feature, Refactoring      | Bug fix only               | Mixed                        |
| **Statistical runs**   | Built-in (N runs + aggregation)    | Manual                     | Manual                       |
| **Visual dashboard**   | Built-in (10+ interactive charts)  | No                         | No                           |
| **GPU tasks**          | ✅ 25 CUDA tasks                    | No                         | No                           |

---

## Quick Start

```powershell
pip install -r requirements.txt

# Amp Deep³ vs Claude Code — full benchmark
python multi_runner.py --runs 3 --agent deep3-vs-claude --timeout 600

# Generate the interactive dashboard
python dashboard.py
```

### Agent Modes

| Flag | Agents | Description |
|------|--------|-------------|
| `--agent both` | Amp (Smart) + Claude Code | Default comparison |
| `--agent deep3-vs-claude` | Amp Deep³ + Claude Code | Maximum reasoning head-to-head |
| `--agent amp-deep3` | Amp Deep³ only | Deep³ = `xhigh` reasoning effort |
| `--agent amp` | Amp (Smart) only | Standard balanced mode |
| `--agent claude` | Claude Code only | Claude Code CLI |

---

## The 100 Tasks

### 🐍 Python (50 tasks)

| Tier | Count | Examples |
|------|-------|---------|
| 🟢 Easy (1–10) | 10 | Interval tree merge, LRU eviction, token bucket, trie autocomplete |
| 🟡 Medium (11–20) | 10 | Async race condition, memoize mutation, Dijkstra zero-weight, FSM validation |
| 🟠 Hard (21–35) | 15 | Red-black tree deletion, A* tie-breaking, B-tree split, segment tree lazy propagation |
| 🔴 Extreme (36–50) | 15 | Compiler lexer, bytecode VM, transaction engine, GC mark-sweep, Raft consensus, type inference |

### ⚙️ C/C++ (25 tasks)

| Tier | Count | Examples |
|------|-------|---------|
| 🟢 Easy (51–55) | 5 | Circular buffer, string tokenizer, matrix multiply, min-heap, hash map |
| 🟡 Medium (56–60) | 5 | SFINAE dispatch, shared_ptr refcount, lock-free stack, iterator invalidation |
| 🟠 Hard (61–68) | 8 | Red-black tree, B+ tree, pool allocator, Tarjan SCC, Pratt parser, NFA→DFA |
| 🔴 Extreme (69–75) | 7 | Mark-compact GC, concurrent hash map, coroutine scheduler, constexpr ray tracer, HAMT |

### 🟢 CUDA (25 tasks)

| Tier | Count | Examples |
|------|-------|---------|
| 🟢 Easy (76–80) | 5 | Vector add, matrix transpose, histogram atomic, prefix sum, 1D convolution |
| 🟡 Medium (81–85) | 5 | Parallel reduction, SpMV CSR, bitonic sort, stream compaction, radix sort |
| 🟠 Hard (86–93) | 8 | Multi-GPU stencil, cooperative groups, unified memory, WMMA GEMM, persistent kernel |
| 🔴 Extreme (94–100) | 7 | Dynamic parallelism, tiled GEMM double buffer, warp BFS, FFT, N-body, ray BVH, MD simulation |

---

## What It Measures

- **Resolution Rate** — Did the agent fix the issue? Fail-to-pass tests must pass.
- **Regression Safety** — Did the agent break anything? Pass-to-pass tests must still pass.
- **Speed** — Wall-clock time per task, per agent.
- **Consistency** — Same result across N independent runs? Variance reveals non-determinism.
- **Per-language breakdown** — Separate tabs for Python, C++, CUDA.
- **Per-difficulty breakdown** — Easy → Medium → Hard → Extreme scaling.

Every measurement is backed by real pytest execution. No LLM-as-judge, no subjective scoring — tests pass or they don't.

---

## Dashboard

`python dashboard.py` generates an interactive HTML dashboard with:

- **Clickable task bars** — Click any task in charts or heatmap to view its code on GitHub
- **Difficulty badges** — 🟢🟡🟠🔴 icons show task difficulty at a glance
- **Tabbed language views** — Separate Python / C++ / CUDA analysis tabs
- **10+ chart types** — Resolution rates, speed comparisons, radar, heatmap, trend analysis

---

## Architecture

```
QuickSWE/
├── multi_runner.py          # Statistical multi-run engine
├── runner.py                # Core task execution & agent invocation
├── dashboard.py             # Interactive HTML dashboard generator
├── requirements.txt         # Python dependencies
├── tasks/                   # 100 self-contained tasks
│   └── task_NNN/
│       ├── src/             # Source code with bug (Python/C++/CUDA)
│       ├── tests/           # pytest suite (fail_to_pass + regression)
│       ├── description.md   # Issue description (given to the agent)
│       └── metadata.json    # Category, difficulty, language, task ID
└── results/                 # Auto-generated run results & dashboard
```

---

## Adding Your Own Agent

```python
# In runner.py → invoke_agent()
elif agent == "my_agent":
    cmd = ["my-agent-cli", "--task", prompt, "--workdir", str(work_dir)]
```

Then run: `python multi_runner.py --runs 3 --agent my_agent`

---

## License

MIT

---

## Citation

```bibtex
@software{quickswe2026,
  title  = {QuickSWE v2: A Multi-Language Stress-Test Benchmark for AI Coding Agents},
  author = {Daniel Zusmanovich},
  year   = {2026},
  url    = {https://github.com/zuwasi/QuickSWE}
}
```
