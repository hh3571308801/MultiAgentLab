"""轨迹数据模型（兼容 Shellloop schema）。

Schema 设计原则：
    1. 完全兼容 Shellloop trajectory-inspector 的 JSON 结构
    2. 使用 Pydantic v2 做类型校验
    3. 字段命名遵循 snake_case（JSON 序列化时自动转换）
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """一次任务运行的最终状态。"""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    MAX_ROUNDS_REACHED = "max_rounds_reached"


class Action(BaseModel):
    """一个结构化的动作（通常对应一次工具调用）。"""

    tool_name: str = Field(..., description="工具名称")
    tool_input: str = Field(..., description="工具输入（字符串）")


class Step(BaseModel):
    """单个步骤的完整记录。

    字段含义：
        - step_id: 全局递增 ID
        - agent_role: 哪个 Agent 产生的这一步
        - thought: LLM 的思考过程
        - action: 这一步要执行的动作（可空，比如 Planner 只思考不执行）
        - observation: 动作的执行结果（可空）
        - token_in: prompt token 数
        - token_out: completion token 数
        - latency_ms: 这一步耗时（毫秒）
        - timestamp: UTC 时间戳
    """

    step_id: int
    agent_role: str
    thought: str
    action: Optional[Action] = None
    observation: Optional[str] = None
    token_in: int = 0
    token_out: int = 0
    latency_ms: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AgentTrace(BaseModel):
    """单个 Agent 在一次运行中的轨迹汇总。

    注意：本项目采用「所有步骤平铺在 trajectory.steps」的简化设计，
    AgentTrace 仅用于未来扩展（按 Agent 聚合）。
    """

    role: str
    model: str
    steps: list[int] = Field(default_factory=list, description="该 Agent 产生的 step_id 列表")


class Trajectory(BaseModel):
    """一次完整运行的轨迹。

    这是 Shellloop trajectory-inspector 能直接解析的格式。
    """

    run_id: str = Field(..., description="一次运行的唯一 UUID")
    task: str = Field(..., description="用户原始任务")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    finished_at: Optional[datetime] = None
    status: RunStatus = RunStatus.SUCCESS
    steps: list[Step] = Field(default_factory=list)
    agents: list[AgentTrace] = Field(default_factory=list)
    final_answer: str = ""
    total_tokens: int = 0
    total_latency_ms: int = 0
    metadata: dict = Field(default_factory=dict)

    def recompute_totals(self) -> None:
        """重新计算总 token 和总耗时。"""
        self.total_tokens = sum(s.token_in + s.token_out for s in self.steps)
        self.total_latency_ms = sum(s.latency_ms for s in self.steps)
        if self.steps:
            self.started_at = self.steps[0].timestamp
            self.finished_at = self.steps[-1].timestamp