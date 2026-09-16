"""Agent 抽象基类。

所有 Agent 必须实现 act() 方法，根据上下文产出一个 Step。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.llm.client import LLMClient
from backend.trajectory.schema import Step


@dataclass
class AgentContext:
    """Agent 共享的上下文。

    包含：
        - task: 用户原始任务
        - history: 历史步骤（已发生的事件）
        - scratchpad: 中间思考 / 计算结果（仅在内存）
        - round: 当前轮次
    """

    task: str
    history: list[Step] = field(default_factory=list)
    scratchpad: dict[str, Any] = field(default_factory=dict)
    round: int = 0

    def add_step(self, step: Step) -> None:
        """追加一个步骤到历史。"""
        self.history.append(step)


class BaseAgent(ABC):
    """所有 Agent 的抽象基类。

    子类必须实现：
        - role: 角色名
        - system_prompt: 系统提示词
        - act(): 核心方法，根据上下文产出一个 Step
    """

    role: str = "base"
    system_prompt: str = "You are a helpful AI agent."

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    @abstractmethod
    async def act(self, context: AgentContext) -> Step:
        """根据当前上下文产生一个 Step。

        Args:
            context: 共享上下文（含历史和中间状态）

        Returns:
            Step: 这一步的 thought + action + observation
        """
        raise NotImplementedError

    def _build_messages(self, context: AgentContext) -> list[dict[str, str]]:
        """构造 LLM 输入消息。

        子类可覆盖此方法以自定义 prompt 模板。
        """
        history_text = self._format_history(context.history)

        user_prompt = (
            f"【用户任务】\n{context.task}\n\n"
            f"【当前轮次】{context.round}\n\n"
            f"【历史步骤】\n{history_text}\n\n"
            f"请基于以上信息，按你的角色职责给出下一步行动。"
        )

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def _format_history(history: list[Step]) -> str:
        """将历史步骤格式化为文本。"""
        if not history:
            return "（暂无）"
        lines = []
        for i, step in enumerate(history, 1):
            lines.append(f"--- 步骤 {i}（{step.agent_role}）---")
            lines.append(f"Thought: {step.thought}")
            if step.action:
                lines.append(
                    f"Action: {step.action.tool_name}({step.action.tool_input})"
                )
            if step.observation:
                lines.append(f"Observation: {step.observation}")
        return "\n".join(lines)