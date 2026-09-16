# MultiAgentLab 🧪

> **可观测、可评测的多 LLM Agent 协作框架**
>
> *Observe, Measure, and Explain Multi-Agent Collaboration*

[![Tests](https://github.com/hh3571308801/MultiAgentLab/actions/workflows/test.yml/badge.svg)](https://github.com/hh3571308801/MultiAgentLab/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Trajectory](https://img.shields.io/badge/Trajectory-Shellloop%20Compatible-orange)](#trajectory-format-compatibility)

> ⚙️ **如果你 fork 了这个项目**，记得把上方 badge 里的 `hh3571308801` 换成你自己的 GitHub 用户名，否则徽章不会显示。

---

## ✨ 项目亮点

**研究问题**：现有 Agent 框架（AutoGPT / LangChain / CrewAI）只关心"能不能跑通"，但 **跑得好不好、为什么失败、哪一步浪费 Token** 缺乏系统化分析。

**本项目核心贡献**：
1. **主动驱动**——从「读别人轨迹」升级为「自己调度多 Agent 协作」
2. **完整观测**——逐步记录 Thought / Action / Observation / Token / 时延
3. **系统评测**——成功率、步骤冗余度、Token 效率、LLM-as-Judge 可解释性评分
4. **失败归因**——自动分析"哪个 Agent、哪一步、为什么"失败
5. **横向对比**——同任务下与 CrewAI / AutoGPT 的 benchmark 对比

---

## 🏗️ 架构总览

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
│         │   (调度器)      │  │  Recorder    │         │
│         └────────┬────────┘  └──────┬───────┘         │
│                  │                  │                 │
│         ┌────────▼────────┐  ┌──────▼───────┐         │
│         │   LLM Client    │  │   SQLite     │         │
│         │ (DeepSeek/Qwen) │  │  + JSON 导出 │         │
│         └─────────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 环境准备

- Python 3.10+
- 一个 LLM API Key（推荐 [DeepSeek](https://platform.deepseek.com)，1 元可跑 5000 轮）

### 2. 安装

```bash
cd MultiAgentLab
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入你的 DEEPSEEK_API_KEY
```

### 3. 启动

```bash
python -m backend.main
# 访问 http://localhost:8000/docs 查看 API 文档
```

### 4. 跑第一个 demo

```bash
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d @examples/math_problem.json
```

预期返回：3 个 Agent（Planner/Executor/Critic）协作解决"小红有 15 元..."数学题的完整轨迹。

---

## 🎯 三种运行模式

根据场景选一个：

| 模式 | 命令 | 用 | 适合 |
|------|------|----|------|
| **🟢 Mock（默认）** | `LLM_PROVIDER=mock pytest` | 0 元 | 本地开发 / CI |
| **🟡 真实 API（一键）** | `python scripts/run_real_demo.py` | ~¥0.001/次 | 截图 / 调试 / 答辩演示 |
| **🔴 真实 API（pytest）** | `LLM_PROVIDER=deepseek pytest -m real_llm` | ~¥0.001/次 | 集成测试 |

### 🟢 Mock 模式（默认）

```bash
# 跑全部测试（不消耗 token）
pytest
# 或 LLM_PROVIDER=mock pytest
```

### 🟡 一键真实 Demo

最快看到真实效果的方式：

```bash
# 1. 配 .env（填 API Key）
cp .env.example .env
# 编辑 .env: 把 LLM_PROVIDER=deepseek 和 DEEPSEEK_API_KEY 填好

# 2. 跑默认任务
python scripts/run_real_demo.py

# 或自定义任务
python scripts/run_real_demo.py "今天西安的天气如何？适合穿什么？"
```

输出：终端打印 emoji 报告 + 完整轨迹 JSON 保存到 `data/trajectories/`。

### 🔴 真实 API 测试（pytest）

```bash
# 配置好 .env 后
LLM_PROVIDER=deepseek pytest -m real_llm -v -s

# -s 让 print() 输出可见（看步骤报告）
# -m real_llm 取消默认的"跳过真实 LLM"过滤
```

> ⚠️ **注意**：`pytest.ini` 默认 `addopts = -m "not real_llm"`，所以普通 `pytest` 不会跑这些测试，避免误消耗 token。

---

## 📸 Real Run Showcase

> ✅ **本展示为真实 DeepSeek API 运行结果**（非 mock）。完整轨迹见 [`examples/sample_real_run.json`](examples/sample_real_run.json)。

### 真实运行效果

**输入任务**（examples/math_problem.json）：
```json
{ "task": "小红有 15 元钱，买了 3 支铅笔，每支铅笔 2 元。她还剩下多少钱？" }
```

**运行命令**：
```bash
python scripts/run_real_demo.py "小红有 15 元钱，买了 3 支铅笔，每支铅笔 2 元。她还剩下多少钱？"
```

**终端输出**：
```
✅ 运行完成
Run ID:       53da92f6-afb6-4024-ae9d-6a6100b2c3d1
任务:         小红有 15 元钱，买了 3 支铅笔，每支铅笔 2 元。她还剩下多少钱？
最终答案:     小红还剩下 9 元。
状态:         success
总步数:       5
总 Token:     3022
总耗时:       15578ms
使用模型:     deepseek-chat
LLM Provider: deepseek

─── 步骤详情 ───

🎯 [1] planner
   💭 这是一道两步计算题：先算买铅笔花掉的总钱数，再用总钱数减去花掉的钱得到剩余。
   📥 生成计划，共 3 个子任务
   📊 tokens=422+107 | latency=7769ms

⚙️  [2] executor
   💭 计算3支铅笔的总花费，需要乘法运算，用计算器
   🔧 calculator(3 * 2)
   📥 6
   📊 tokens=542+34 | latency=3016ms

⚙️  [3] executor
   💭 已知总花费为6元，计算剩余钱数需要做减法，用计算器
   🔧 calculator(15 - 6)
   📥 9
   📊 tokens=582+38 | latency=1975ms

⚙️  [4] executor
   💭 验证答案：3支铅笔每支2元共6元，15-6=9元，剩余9元。结果合理，无需调用工具。
   📊 tokens=623+48 | latency=1846ms

🔍 [5] critic
   💭 计算过程正确：3支铅笔每支2元共6元，15-6=9元。使用了计算器工具验证，逻辑清晰，答案准确，完整回答了用户问题。
   📥 评判结果: 满意
   📊 tokens=561+65 | latency=972ms
```

**响应摘要**：
```json
{
  "run_id": "53da92f6-afb6-4024-ae9d-6a6100b2c3d1",
  "task": "小红有 15 元钱，买了 3 支铅笔，每支铅笔 2 元。她还剩下多少钱？",
  "status": "success",
  "rounds_used": 1,
  "total_steps": 5,
  "total_tokens": 3022,
  "total_latency_ms": 15578,
  "final_answer": "小红还剩下 9 元。",
  "llm_provider": "deepseek",
  "llm_model": "deepseek-chat"
}
```

> 💰 **单次运行成本约 ¥0.004**（3022 tokens），充 ¥10 可跑约 2500 次此类任务。

### 完整轨迹

完整的多 Agent 轨迹 JSON 见 [`examples/sample_real_run.json`](examples/sample_real_run.json)，包含每一步的 `thought` / `action` / `observation` / token 消耗 / 时延。

### 协作时间线

```
Round 1 ─────────────────────────────────────────────────
   │
   ├─ [Step 1] 🎯 Planner (deepseek-chat)
   │           Thought: 这是一道两步计算题：先算买铅笔花掉的总钱数，
   │                    再用总钱数减去花掉的钱得到剩余。
   │           Plan: [计算3支铅笔的总花费, 计算剩余钱数, 验证答案]
   │           Tokens: 422 in / 107 out | 7769ms
   │
   ├─ [Step 2] ⚙️ Executor (deepseek-chat)
   │           Thought: 计算3支铅笔的总花费，需要乘法运算，用计算器
   │           Action: calculator("3 * 2")
   │           Observation: 6
   │           Tokens: 542 in / 34 out | 3016ms
   │
   ├─ [Step 3] ⚙️ Executor (deepseek-chat)
   │           Thought: 已知总花费为6元，计算剩余钱数需要做减法
   │           Action: calculator("15 - 6")
   │           Observation: 9
   │           Tokens: 582 in / 38 out | 1975ms
   │
   ├─ [Step 4] ⚙️ Executor (deepseek-chat)
   │           Thought: 验证答案：3支铅笔每支2元共6元，15-6=9元，
   │                    剩余9元。结果合理，无需调用工具。
   │           Tokens: 623 in / 48 out | 1846ms
   │
   └─ [Step 5] 🔍 Critic (deepseek-chat)
               Thought: 计算过程正确：3支铅笔每支2元共6元，15-6=9元。
                        使用了计算器工具验证，逻辑清晰，答案准确。
               Satisfied: ✅ true
               Answer: 小红还剩下 9 元。
               Tokens: 561 in / 65 out | 972ms

Total: 5 steps | 3022 tokens | 15578ms | ✅ SUCCESS
```

### 如何复现这个结果

```bash
# 1. 配置 API Key（.env 已被 .gitignore 保护，不会泄露）
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 2. 一键运行同一个任务
python scripts/run_real_demo.py "小红有 15 元钱，买了 3 支铅笔，每支铅笔 2 元。她还剩下多少钱？"

# 3. 查看完整轨迹
cat data/trajectories/{run_id}.json
```

---

## 📂 目录结构

```
MultiAgentLab/
├── backend/                  # 后端核心
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置加载（.env）
│   ├── llm/
│   │   └── client.py        # LLM 客户端（DeepSeek/OpenAI 兼容）
│   ├── agents/
│   │   ├── base.py          # Agent 基类
│   │   ├── planner.py       # 任务规划 Agent
│   │   ├── executor.py      # 工具执行 Agent
│   │   └── critic.py        # 反思批评 Agent
│   ├── tools/
│   │   ├── calculator.py    # 计算器工具
│   │   └── search.py        # 搜索工具（可选）
│   ├── trajectory/
│   │   ├── schema.py        # 轨迹数据模型（兼容 Shellloop）
│   │   └── recorder.py      # 轨迹记录器
│   ├── orchestrator.py      # 多 Agent 调度核心
│   └── api/
│       └── routes.py        # API 路由
├── frontend/                # Vue3 前端（占位，待开发）
├── examples/                # 示例任务
│   ├── math_problem.json
│   ├── weather_query.json
│   ├── summary_task.json
│   └── sample_real_run.json # 真实 DeepSeek 运行轨迹示例 ✅
├── scripts/                 # 辅助脚本
│   └── run_real_demo.py     # 一键跑真实 LLM Demo
├── tests/
│   ├── test_smoke.py        # 冒烟测试（mock 模式）
│   ├── test_parse_robustness.py # LLM 输出解析鲁棒性测试
│   └── test_real_deepseek.py    # 真实 DeepSeek 集成测试（需 -m real_llm）
├── docs/
│   ├── architecture.md      # 详细架构设计
│   ├── HOW_TO_REPLACE_MOCK.md # 替换 mock 为真实运行的指南
│   ├── PUBLISH_TO_GITHUB.md # 发布到 GitHub 的完整步骤
│   └── images/              # 真实运行截图占位
├── .github/
│   └── workflows/
│       └── test.yml         # CI：自动跑 pytest（mock 模式）
├── pytest.ini
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE                  # MIT
└── README.md
```

---

## 🎯 Roadmap（已规划 / 进行中 / 待办）

### ✅ v0.1（MVP 骨架 — 当前阶段）
- [x] FastAPI 框架 + 多 Agent 调度
- [x] Planner / Executor / Critic 三角色
- [x] 轨迹完整记录（兼容 Shellloop schema）
- [x] DeepSeek / OpenAI 双 provider
- [x] 计算器工具

### 🔜 v0.2（可视化）
- [ ] Vue3 + ECharts 轨迹时间线
- [ ] Token 流图
- [ ] 失败节点高亮

### 🔜 v0.3（评测模块）
- [ ] 成功率 / 步骤冗余度 / Token 效率指标
- [ ] LLM-as-Judge 可解释性评分
- [ ] 失败归因（哪个 Agent、哪一步、为什么）

### 🔜 v0.4（横向对比）
- [ ] 与 CrewAI / AutoGPT 同任务对比 benchmark
- [ ] 评测报告自动生成（PDF / Markdown）

### 🔜 v0.5（论文配套）
- [ ] 在 5 个任务 × 3 个框架上的实验数据
- [ ] 论文初稿（投稿 EMNLP Findings / ACL Workshop）

---

## 🧬 Trajectory Format Compatibility

本项目的轨迹 JSON Schema 与你之前做的 [Shellloop trajectory-inspector](https://github.com/DZW131/shellloop) **完全兼容**：

```json
{
  "run_id": "uuid",
  "task": "用户原始任务",
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
          "thought": "我需要把任务分解成子任务...",
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
  "final_answer": "答案是 4",
  "total_tokens": 540,
  "total_latency_ms": 12000
}
```

老 Shellloop 项目产生的 JSON 可以直接被本项目读取分析，**轨迹数据完全可复用**。

---

## 📊 预期性能指标（答辩可用数据）

| 任务 | 框架 | 成功率 | 平均 Token | 平均步骤 |
|------|------|--------|----------|---------|
| 数学推理 | **MultiAgentLab** | ~85% | 1200 | 4.2 |
| 数学推理 | CrewAI | ~78% | 1800 | 5.5 |
| 信息检索 | **MultiAgentLab** | ~82% | 950 | 3.8 |
| 信息检索 | AutoGPT | ~65% | 2400 | 8.1 |

> 注：以上为预期目标值，实际数据待 v0.4 阶段生成。

---

## 🛠️ 开发约定

- **代码风格**：PEP 8 + 类型注解 + Google Style Docstring
- **提交规范**：Conventional Commits（`feat:` / `fix:` / `docs:` / `test:`）
- **测试**：pytest + httpx.AsyncClient
- **日志**：标准 logging + JSON 格式输出

---

## 📜 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 👤 作者

西北大学智算工程学院 计算机科学与技术 2024 级
方向：可解释 Multi-Agent 系统 / LLM 评测
邮箱：联系 GitHub Issues