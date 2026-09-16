# Architecture Design Document

> This document explains the design motivation, technology choices, module boundaries, and extension points of MultiAgentLab.

---

## 1. Research Motivation

### 1.1 Pain points of existing Agent frameworks

| Framework | Strengths | Weaknesses (research gaps) |
|-----------|-----------|----------------------------|
| AutoGPT | Fully autonomous | Uncontrollable trajectory, token explosion, no evaluation |
| LangChain | Flexible | Too low-level, lacks a "collaboration" abstraction |
| CrewAI | Role-based | No failure analysis, not observable |
| AgentVerse | Multi-agent | No evaluation, not explainable |

**Common shortcomings**:
1. They only care about "can it run end-to-end", not "**how well it runs**"
2. Lack systematic **observability** (trajectory visualization)
3. Lack **explainability** (why did it fail)
4. Lack **horizontal evaluation** (which is better: A vs B vs C)

### 1.2 Core research question of this project

> **How can we systematically observe, evaluate, and explain the multi-LLM-Agent collaboration process?**

Three sub-questions:
- Q1: Can a unified schema record the full trajectory of multi-agent collaboration?
- Q2: Can a set of metrics be designed to quantify "collaboration quality"?
- Q3: Can we automatically attribute failure causes and suggest improvements?

---

## 2. Module Layout

```
backend/
├── config.py            # Single responsibility: env var loading & validation
├── llm/
│   └── client.py        # Single responsibility: LLM API calls (multi-provider abstraction)
├── agents/
│   ├── base.py          # Abstract base class: unified interface for all Agents
│   ├── planner.py       # Task planning
│   ├── executor.py      # Tool execution
│   └── critic.py        # Reflection / critic
├── tools/
│   ├── calculator.py    # Atomic tool 1
│   └── search.py        # Atomic tool 2
├── trajectory/
│   ├── schema.py        # Trajectory data model (Pydantic)
│   └── recorder.py      # Trajectory writer / exporter
├── orchestrator.py      # Scheduling core: message passing between Agents
└── api/
    └── routes.py        # HTTP layer
```

### 2.1 Agent base class (base.py)

```python
class BaseAgent(ABC):
    role: str  # "planner" / "executor" / "critic"
    system_prompt: str

    @abstractmethod
    async def act(self, context: Context) -> Step:
        """Produce a Step (thought + action) from the current context"""
        ...

    @abstractmethod
    def parse_action(self, raw: str) -> Action:
        """Parse a structured action from LLM output"""
        ...
```

### 2.2 Orchestrator scheduling flow

```
┌─────────┐    ┌──────────┐    ┌──────────┐
│  START  │───▶│ PLANNER  │───▶│ EXECUTOR │
└─────────┘    └────┬─────┘    └────┬─────┘
                    │               │
                    ▼               ▼
               Plan List       Tool Calls
                    │               │
                    └───────┬───────┘
                            ▼
                    ┌──────────┐
                    │  CRITIC  │
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Satisfied → END         Not satisfied → REPLAN
```

Max round limit (to avoid infinite loops): default 5, configurable.

---

## 3. Data Model

### 3.1 Trajectory schema (Shellloop-compatible)

See `backend/trajectory/schema.py`. Full fields:

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | UUID | Unique ID for one task run |
| `task` | string | Original user task description |
| `agents` | List[AgentTrace] | List of participating Agents |
| `steps` | List[Step] | All steps in chronological order |
| `final_answer` | string | Final output |
| `status` | enum | success / failed / timeout |
| `total_tokens` | int | Total tokens consumed |
| `total_latency_ms` | int | Total time (milliseconds) |

### 3.2 Step detailed fields

```python
class Step(BaseModel):
    step_id: int
    agent_role: str  # planner / executor / critic
    thought: str  # Reasoning process
    action: Optional[Action]  # Tool invocation
    observation: Optional[str]  # Tool return value
    token_in: int
    token_out: int
    latency_ms: int
    timestamp: datetime
```

---

## 4. Evaluation Metric Design (v0.3 stage)

| Metric | Formula | Meaning |
|--------|---------|---------|
| Success rate (SR) | successful runs / total runs | Basic capability |
| Avg steps (AvgSteps) | total steps / successful runs | Efficiency |
| Token efficiency (TokEff) | success count / total tokens | Economy |
| Step redundancy (Redundancy) | 1 - effective steps / total steps | Reflection capability |
| Hallucination rate | LLM-as-Judge hallucination count / total steps | Accuracy |
| Explainability | mean LLM-as-Judge score | Transparency |

---

## 5. Extension Points

1. **Add a new Agent**: inherit `BaseAgent` and add a file under `agents/`
2. **Add a new tool**: add the function under `tools/` and register it in `executor.py`
3. **Swap LLM provider**: change `LLM_PROVIDER` in `.env`
4. **Plug in evaluation**: implement a `backend/evaluation/` sub-module