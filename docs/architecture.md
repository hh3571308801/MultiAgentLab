# 架构设计文档

> 本文档面向研究生面试 / 答辩场景，详细说明 MultiAgentLab 的设计动机、技术选型、模块边界与扩展点。

---

## 一、研究动机

### 1.1 现有 Agent 框架的痛点

| 框架 | 优点 | 缺点（研究空白）|
|------|------|----------------|
| AutoGPT | 全自主 | 轨迹不可控、Token 爆炸、缺乏评测 |
| LangChain | 灵活 | 太底层，缺少"协作"抽象 |
| CrewAI | 角色化 | 缺乏失败分析、不可观测 |
| AgentVerse | 多 Agent | 没有评测、不可解释 |

**共同缺陷**：
1. 只关心"能不能跑通"，不关心"**跑得好不好**"
2. 缺乏系统化的**可观测性**（轨迹可视化）
3. 缺乏**可解释性**（为什么失败）
4. 缺乏**横向评测**（A vs B vs C 哪个更好）

### 1.2 本项目的核心研究问题

> **如何系统化地观测、评测、可解释多 LLM Agent 协作过程？**

三个子问题：
- Q1：能否用一个统一 schema 记录多 Agent 协作的完整轨迹？
- Q2：能否设计一组指标量化"协作质量"？
- Q3：能否自动归因失败原因，并给出改进建议？

---

## 二、模块划分

```
backend/
├── config.py            # 单一职责：环境变量加载与校验
├── llm/
│   └── client.py        # 单一职责：LLM API 调用（多 provider 抽象）
├── agents/
│   ├── base.py          # 抽象基类：所有 Agent 的统一接口
│   ├── planner.py       # 任务规划
│   ├── executor.py      # 工具执行
│   └── critic.py        # 反思批评
├── tools/
│   ├── calculator.py    # 原子工具 1
│   └── search.py        # 原子工具 2
├── trajectory/
│   ├── schema.py        # 轨迹数据模型（Pydantic）
│   └── recorder.py      # 轨迹写入/导出
├── orchestrator.py      # 调度核心：Agent 间消息传递
└── api/
    └── routes.py        # HTTP 层
```

### 2.1 Agent 基类（base.py）

```python
class BaseAgent(ABC):
    role: str  # "planner" / "executor" / "critic"
    system_prompt: str

    @abstractmethod
    async def act(self, context: Context) -> Step:
        """根据当前上下文产出一个 Step（thought + action）"""
        ...

    @abstractmethod
    def parse_action(self, raw: str) -> Action:
        """从 LLM 输出解析结构化动作"""
        ...
```

### 2.2 Orchestrator 调度流程

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
        满意 → END             不满意 → REPLAN
```

最大轮数限制（避免死循环）：默认 5 轮，可配置。

---

## 三、数据模型

### 3.1 轨迹 Schema（兼容 Shellloop）

参见 `backend/trajectory/schema.py`。完整字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `run_id` | UUID | 一次任务运行的唯一 ID |
| `task` | string | 用户原始任务描述 |
| `agents` | List[AgentTrace] | 参与的 Agent 列表 |
| `steps` | List[Step] | 按时间顺序的所有步骤 |
| `final_answer` | string | 最终输出 |
| `status` | enum | success / failed / timeout |
| `total_tokens` | int | 总消耗 Token |
| `total_latency_ms` | int | 总耗时（毫秒）|

### 3.2 Step 详细字段

```python
class Step(BaseModel):
    step_id: int
    agent_role: str  # planner / executor / critic
    thought: str  # 思考过程
    action: Optional[Action]  # 调用的工具
    observation: Optional[str]  # 工具返回
    token_in: int
    token_out: int
    latency_ms: int
    timestamp: datetime
```

---

## 四、评测指标设计（v0.3 阶段）

| 指标 | 公式 | 意义 |
|------|------|------|
| 成功率 (SR) | 成功运行数 / 总运行数 | 基本能力 |
| 平均步骤数 (AvgSteps) | 总步骤 / 成功运行数 | 效率 |
| Token 效率 (TokEff) | 成功数 / 总 Token | 经济性 |
| 步骤冗余度 (Redundancy) | 1 - 有效步骤 / 总步骤 | 反思能力 |
| 幻觉率 (Hallucination) | LLM-as-Judge 判为幻觉 / 总步骤 | 准确性 |
| 可解释性 (Explainability) | LLM-as-Judge 评分均值 | 透明度 |

---

## 五、扩展点

1. **新增 Agent**：继承 `BaseAgent`，在 `agents/` 添加文件
2. **新增工具**：在 `tools/` 添加函数，在 `executor.py` 注册
3. **替换 LLM Provider**：修改 `.env` 中 `LLM_PROVIDER` 即可
4. **接入评测**：实现 `backend/evaluation/` 子模块

---

## 六、面试话术（30 秒 / 1 分钟 / 5 分钟三个版本）

### 30 秒版
> "我做的是 MultiAgentLab，一个多 LLM Agent 协作框架。核心创新是把'观测-评测-归因'一体化：跑完一个任务能直接告诉你哪个 Agent、哪一步、为什么失败，以及和 CrewAI 比起来好在哪。"

### 1 分钟版
> "现有 Agent 框架都只关心能不能跑通，缺系统化分析。我的项目 MultiAgentLab 用 Planner / Executor / Critic 三角色协作，每一步 thought、action、Token、时延全记录，然后用 LLM-as-Judge 自动评测并归因失败。整套轨迹 JSON 兼容我之前做的 Shellloop 平台，所以新项目不是从零开始，是迭代升级。"

### 5 分钟版
（自由发挥，从动机→架构→实验→创新点→未来工作）