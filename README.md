# MultiAgentLab 🧪

> **An Observable, Evaluable Multi-LLM-Agent Collaboration Framework**
>
> *Observe, Measure, and Explain Multi-Agent Collaboration*

[![Tests](https://github.com/hh3571308801/MultiAgentLab/actions/workflows/test.yml/badge.svg)](https://github.com/hh3571308801/MultiAgentLab/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Trajectory](https://img.shields.io/badge/Trajectory-Shellloop%20Compatible-orange)](#trajectory-format-compatibility)

> ⚙️ **If you fork this repo**, remember to replace `hh3571308801` in the badges above with your own GitHub username, otherwise the badges won't render.

---

## ✨ Highlights

**The research problem**: Existing Agent frameworks (AutoGPT / LangChain / CrewAI) only care about "can it run end-to-end", but **how well it runs, why it fails, and which step wastes tokens** still lack systematic analysis.

**Core contributions of this project**:
1. **Proactive orchestration** — upgrade from "reading other people's trajectories" to "driving multi-agent collaboration yourself"
2. **Full observability** — record Thought / Action / Observation / Token / Latency step by step
3. **Systematic evaluation** — success rate, step redundancy, token efficiency, LLM-as-Judge explainable scoring
4. **Failure attribution** — automatic analysis of "which Agent, which step, and why"
5. **Horizontal comparison** — benchmark against CrewAI / AutoGPT on the same tasks

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue3 + ECharts)            │
│              Timeline · Token Flow · Failure Map        │
└────────────────────────┬────────────────────────────────┘
                         │ REST / SSE
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Planner    │  │   Executor   │  │    Critic    │  │
│  │   Agent      │  │   Agent      │  │    Agent     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │          │
│         └─────────┬───────┴─────────┬───────┘          │
│                   ▼                 ▼                  │
│         ┌─────────────────┐  ┌──────────────┐         │
│         │   Orchestrator  │  │  Trajectory  │         │
│         │   (Scheduler)   │  │  Recorder    │         │
│         └────────┬────────┘  └──────┬───────┘         │
│                  │                  │                 │
│         ┌────────▼────────┐  ┌──────▼───────┐         │
│         │   LLM Client    │  │   SQLite     │         │
│         │ (DeepSeek/Qwen) │  │  + JSON Dump │         │
│         └─────────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- An LLM API key (recommend [DeepSeek](https://platform.deepseek.com) — ¥1 can run ~5000 tasks)

### 2. Install

```bash
cd MultiAgentLab
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in your DEEPSEEK_API_KEY
```

### 3. Start the server

```bash
python -m backend.main
# Visit http://localhost:8000/docs for the API documentation
```

### 4. Run your first demo

```bash
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d @examples/math_problem.json
```

Expected output — three agents (Planner / Executor / Critic) collaborating to solve the math problem "Alice has 15 dollars, bought 3 pencils at 2 dollars each. How much does she have left?" with a complete trajectory.

---

## 🎯 Three Run Modes

Pick one based on your scenario:

| Mode | Command | Cost | Use for |
|------|---------|------|---------|
| **🟢 Mock (default)** | `LLM_PROVIDER=mock pytest` | Free | Local dev / CI |
| **🟡 Real API (one-click)** | `python scripts/run_real_demo.py` | ~¥0.001 / run | Screenshots / Debug / Integration check |
| **🔴 Real API (pytest)** | `LLM_PROVIDER=deepseek pytest -m real_llm` | ~¥0.001 / run | Integration tests |

### 🟢 Mock mode (default)

```bash
# Run all tests (no tokens consumed)
pytest
# or: LLM_PROVIDER=mock pytest
```

### 🟡 One-click real demo

The fastest way to see real output:

```bash
# 1. Configure .env (fill in API Key)
cp .env.example .env
# Edit .env: set LLM_PROVIDER=deepseek and fill in DEEPSEEK_API_KEY

# 2. Run the default task
python scripts/run_real_demo.py

# Or run a custom task
python scripts/run_real_demo.py "How is the weather in Xi'an today? What should I wear?"
```

Output: an emoji-formatted report is printed to the terminal and the full trajectory JSON is saved under `data/trajectories/`.

### 🔴 Real API tests (pytest)

```bash
# After .env is configured
LLM_PROVIDER=deepseek pytest -m real_llm -v -s

# -s makes print() output visible (see the step report)
# -m real_llm disables the default "skip real LLM" filter
```

> ⚠️ **Note**: `pytest.ini` defaults to `addopts = -m "not real_llm"`, so a plain `pytest` will skip these tests and avoid accidental token consumption.

---

## 📸 Real Run Showcase

> ✅ **This showcase is the result of a real DeepSeek API run** (not mock). The complete trajectory is available at [`examples/sample_real_run.json`](examples/sample_real_run.json).

### Real run output

**Input task** (examples/math_problem.json):
```json
{ "task": "Alice has 15 dollars, bought 3 pencils at 2 dollars each. How much does she have left?" }
```

**Run command**:
```bash
python scripts/run_real_demo.py "Alice has 15 dollars, bought 3 pencils at 2 dollars each. How much does she have left?"
```

**Terminal output**:
```
✅ Run complete
Run ID:       53da92f6-afb6-4024-ae9d-6a6100b2c3d1
Task:         Alice has 15 dollars, bought 3 pencils at 2 dollars each. How much does she have left?
Final answer: Alice has 9 dollars left.
Status:       success
Total steps:  5
Total tokens: 3022
Total time:   15578ms
Model:        deepseek-chat
LLM Provider: deepseek

─── Step Details ───

🎯 [1] planner
   💭 This is a two-step calculation: first compute the total cost of the pencils,
      then subtract that cost from the total to get the remainder.
   📥 Generated a plan with 3 sub-tasks
   📊 tokens=422+107 | latency=7769ms

⚙️  [2] executor
   💭 Computing the total cost of 3 pencils requires multiplication, so I'll use the calculator
   🔧 calculator(3 * 2)
   📥 6
   📊 tokens=542+34 | latency=3016ms

⚙️  [3] executor
   💭 The total cost is 6 dollars, so computing the remainder requires subtraction via the calculator
   🔧 calculator(15 - 6)
   📥 9
   📊 tokens=582+38 | latency=1975ms

⚙️  [4] executor
   💭 Verify the answer: 3 pencils at 2 dollars each cost 6 dollars; 15 - 6 = 9 dollars,
      with 9 dollars remaining. The result is reasonable — no tool call needed.
   📊 tokens=623+48 | latency=1846ms

🔍 [5] critic
   💭 The calculation is correct: 3 pencils at 2 dollars each cost 6 dollars; 15 - 6 = 9 dollars.
      The tool was used to verify the math; the reasoning is clear, the answer accurate,
      and the user's question was fully addressed.
   📥 Judgment: Satisfied
   📊 tokens=561+65 | latency=972ms
```

**Response summary**:
```json
{
  "run_id": "53da92f6-afb6-4024-ae9d-6a6100b2c3d1",
  "task": "Alice has 15 dollars, bought 3 pencils at 2 dollars each. How much does she have left?",
  "status": "success",
  "rounds_used": 1,
  "total_steps": 5,
  "total_tokens": 3022,
  "total_latency_ms": 15578,
  "final_answer": "Alice has 9 dollars left.",
  "llm_provider": "deepseek",
  "llm_model": "deepseek-chat"
}
```

> 💰 **Each run costs about ¥0.004** (3022 tokens); a ¥10 top-up runs roughly 2,500 such tasks.

### Full trajectory

The complete multi-agent trajectory JSON is available at [`examples/sample_real_run.json`](examples/sample_real_run.json), containing every step's `thought` / `action` / `observation` / token consumption / latency.

### Collaboration timeline

```
Round 1 ─────────────────────────────────────────────────
   │
   ├─ [Step 1] 🎯 Planner (deepseek-chat)
   │           Thought: This is a two-step calculation: first compute the total cost
   │                    of the pencils, then subtract it from the total to get the remainder.
   │           Plan: [compute total pencil cost, compute remainder, verify answer]
   │           Tokens: 422 in / 107 out | 7769ms
   │
   ├─ [Step 2] ⚙️ Executor (deepseek-chat)
   │           Thought: Computing the total cost of 3 pencils requires multiplication
   │           Action: calculator("3 * 2")
   │           Observation: 6
   │           Tokens: 542 in / 34 out | 3016ms
   │
   ├─ [Step 3] ⚙️ Executor (deepseek-chat)
   │           Thought: The total cost is 6 dollars, so computing the remainder requires subtraction
   │           Action: calculator("15 - 6")
   │           Observation: 9
   │           Tokens: 582 in / 38 out | 1975ms
   │
   ├─ [Step 4] ⚙️ Executor (deepseek-chat)
   │           Thought: Verify the answer: 3 pencils at 2 dollars each cost 6 dollars;
   │                    15 - 6 = 9 dollars, 9 dollars remaining. The result is reasonable.
   │           Tokens: 623 in / 48 out | 1846ms
   │
   └─ [Step 5] 🔍 Critic (deepseek-chat)
               Thought: The calculation is correct: 3 pencils at 2 dollars each cost
                        6 dollars; 15 - 6 = 9 dollars. The calculator tool was used
                        to verify; the reasoning is clear and the answer is accurate.
               Satisfied: ✅ true
               Answer: Alice has 9 dollars left.
               Tokens: 561 in / 65 out | 972ms

Total: 5 steps | 3022 tokens | 15578ms | ✅ SUCCESS
```

### How to reproduce

```bash
# 1. Configure your API Key (.env is protected by .gitignore and won't be leaked)
cp .env.example .env
# Edit .env and fill in DEEPSEEK_API_KEY

# 2. Run the same task with one command
python scripts/run_real_demo.py "Alice has 15 dollars, bought 3 pencils at 2 dollars each. How much does she have left?"

# 3. View the full trajectory
cat data/trajectories/{run_id}.json
```

---

## 📂 Project Structure

```
MultiAgentLab/
├── backend/                  # Backend core
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Config loader (.env)
│   ├── llm/
│   │   └── client.py        # LLM client (DeepSeek / OpenAI compatible)
│   ├── agents/
│   │   ├── base.py          # Agent base class
│   │   ├── planner.py       # Task planning agent
│   │   ├── executor.py      # Tool execution agent
│   │   └── critic.py        # Reflection / critic agent
│   ├── tools/
│   │   ├── calculator.py    # Calculator tool
│   │   └── search.py        # Search tool (optional)
│   ├── trajectory/
│   │   ├── schema.py        # Trajectory data model (Shellloop-compatible)
│   │   └── recorder.py      # Trajectory recorder
│   ├── orchestrator.py      # Multi-agent scheduling core
│   └── api/
│       └── routes.py        # API routes
├── frontend/                # Vue3 frontend (placeholder)
├── examples/                # Example tasks
│   ├── math_problem.json
│   ├── weather_query.json
│   ├── summary_task.json
│   └── sample_real_run.json # Sample real DeepSeek trajectory ✅
├── scripts/                 # Helper scripts
│   └── run_real_demo.py     # One-click real LLM demo runner
├── tests/
│   ├── test_smoke.py        # Smoke tests (mock mode)
│   ├── test_parse_robustness.py # LLM output parsing robustness tests
│   └── test_real_deepseek.py    # Real DeepSeek integration test (needs -m real_llm)
├── docs/
│   ├── architecture.md      # Detailed architecture design
│   ├── HOW_TO_REPLACE_MOCK.md # Guide to replace mock with real runs
│   ├── PUBLISH_TO_GITHUB.md # Complete steps to publish on GitHub
│   └── images/              # Real-run screenshot placeholders
├── .github/
│   └── workflows/
│       └── test.yml         # CI: auto-run pytest (mock mode)
├── pytest.ini
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE                  # MIT
└── README.md
```

---

## 🎯 Roadmap (Planned / In progress / Backlog)

### ✅ v0.1 (MVP skeleton — current stage)
- [x] FastAPI framework + multi-agent scheduling
- [x] Planner / Executor / Critic three-role loop
- [x] Full trajectory recording (compatible with Shellloop schema)
- [x] DeepSeek / OpenAI dual providers
- [x] Calculator tool

### 🔜 v0.2 (Visualization)
- [ ] Vue3 + ECharts trajectory timeline
- [ ] Token flow diagram
- [ ] Failure node highlight

### 🔜 v0.3 (Evaluation module)
- [ ] Success rate / step redundancy / token efficiency metrics
- [ ] LLM-as-Judge explainable scoring
- [ ] Failure attribution (which Agent, which step, why)

### 🔜 v0.4 (Horizontal comparison)
- [ ] Benchmark against CrewAI / AutoGPT on the same tasks
- [ ] Auto-generated evaluation reports (PDF / Markdown)

### 🔜 v0.5 (Paper bundle)
- [ ] Experiments on 5 tasks × 3 frameworks
- [ ] Paper draft (target: EMNLP Findings / ACL Workshop)

---

## 🧬 Trajectory Format Compatibility

The trajectory JSON schema of this project is **fully compatible** with [Shellloop trajectory-inspector](https://github.com/DZW131/shellloop):

```json
{
  "run_id": "uuid",
  "task": "user's original task",
  "started_at": "2026-09-16T14:30:00Z",
  "finished_at": "2026-09-16T14:30:12Z",
  "status": "success",
  "agents": [
    {
      "role": "planner",
      "model": "deepseek-chat",
      "steps": [
        {
          "step_id": 1,
          "thought": "I need to break the task into sub-tasks...",
          "action": null,
          "observation": null,
          "token_in": 120,
          "token_out": 80,
          "latency_ms": 1500,
          "timestamp": "2026-09-16T14:30:01Z"
        }
      ]
    }
  ],
  "final_answer": "The answer is 4",
  "total_tokens": 540,
  "total_latency_ms": 12000
}
```

JSON produced by the legacy Shellloop project can be directly read and analyzed by this project — **trajectory data is fully reusable**.

---

## 📊 Expected Performance Metrics

| Task | Framework | Success rate | Avg tokens | Avg steps |
|------|-----------|--------------|------------|-----------|
| Math reasoning | **MultiAgentLab** | ~85% | 1200 | 4.2 |
| Math reasoning | CrewAI | ~78% | 1800 | 5.5 |
| Information retrieval | **MultiAgentLab** | ~82% | 950 | 3.8 |
| Information retrieval | AutoGPT | ~65% | 2400 | 8.1 |

> Note: the values above are target goals; real numbers will be available after v0.4.

---

## 🛠️ Development Conventions

- **Code style**: PEP 8 + type hints + Google-style docstrings
- **Commit convention**: Conventional Commits (`feat:` / `fix:` / `docs:` / `test:`)
- **Testing**: pytest + httpx.AsyncClient
- **Logging**: standard logging + JSON-formatted output

---

## 📜 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

An undergraduate student of Computer Science, interested in explainable multi-agent systems and LLM evaluation.
Contact: open a GitHub Issue