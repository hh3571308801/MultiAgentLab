"""Critic Agent：负责评判执行结果，决定是否需要重规划。

鲁棒性设计同 Planner / Executor。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from backend.agents.base import AgentContext, BaseAgent
from backend.agents.planner import _clean_json_text
from backend.trajectory.schema import Step

logger = logging.getLogger(__name__)


# Critic 的系统提示词（v2: few-shot + 强约束 + 修正编号）
CRITIC_SYSTEM_PROMPT = """你是 MultiAgentLab 框架的 Critic Agent，职责是评判 Executor 的执行结果是否满足用户任务，并决定是否需要重规划。

【严格输出规则 - 必须遵守】
1. 你的唯一输出必须是合法 JSON，不能包含任何其他文字、解释、Markdown 代码块标记
2. 不要用 ```json 或 ``` 包裹你的输出
3. 思考过程放在 thought 字段里

【输出格式】
{"thought":"你的评判推理","satisfied":true或false,"answer":"如果满意给出最终答案","suggestion":"如果不满意给出改进建议"}

【评判标准】
1. 最终答案是否逻辑正确
2. 计算结果是否准确（如有）
3. 是否完整回答了用户问题
4. 答案是否简洁明了

【Few-shot 示例 1 - 满意】
历史步骤：计算 15-3*2=9
你的输出：
{"thought":"数学计算正确","satisfied":true,"answer":"小红还剩 9 元","suggestion":""}

【Few-shot 示例 2 - 不满意】
历史步骤：Executor 没有调用工具，直接猜了答案
你的输出：
{"thought":"答案缺少验证过程","satisfied":false,"answer":"","suggestion":"请用 calculator 工具重新计算并验证"}

【决策原则】
- satisfied=true：表示当前结果已经满足用户要求，可以结束
- satisfied=false：必须给出具体可执行的 suggestion，便于下一轮 Planner 改进
"""


class CriticAgent(BaseAgent):
    """反思批评 Agent。"""

    role = "critic"
    system_prompt = CRITIC_SYSTEM_PROMPT

    async def act(self, context: AgentContext) -> Step:
        """评判当前结果，带重试机制。"""
        base_messages = self._build_messages(context)
        last_error: str | None = None

        for attempt in range(2):
            messages = list(base_messages)
            if attempt == 1 and last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"⚠️ 你上一次的输出无法解析为合法 JSON。\n"
                            f"错误信息：{last_error}\n"
                            f"请严格按格式输出纯 JSON，不要加任何额外文字或 markdown。"
                        ),
                    }
                )

            response = await self.llm.chat(messages, temperature=0.1)
            thought, satisfied, answer, suggestion, error = self._parse_verdict(
                response.content
            )

            if error is None:
                context.scratchpad["critic_satisfied"] = satisfied
                context.scratchpad["final_answer"] = answer
                context.scratchpad["critic_suggestion"] = suggestion

                step = Step(
                    step_id=len(context.history) + 1,
                    agent_role=self.role,
                    thought=thought,
                    action=None,
                    observation=f"评判结果: {'满意' if satisfied else '不满意'}",
                    token_in=response.token_in,
                    token_out=response.token_out,
                    latency_ms=response.latency_ms,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                context.add_step(step)
                return step

            last_error = error
            logger.warning("Critic 解析失败 (attempt %d/2): %s", attempt + 1, error)

        # 兜底
        logger.error("Critic 重试 2 次仍无法解析: %s", response.content[:200])
        # 兜底策略：不满意但提供兜底 answer
        step = Step(
            step_id=len(context.history) + 1,
            agent_role=self.role,
            thought=f"[解析失败] LLM 输出无法解析。原始输出: {response.content[:300]}",
            action=None,
            observation="⚠️ Critic 输出无法解析，默认判定为不满意",
            token_in=response.token_in,
            token_out=response.token_out,
            latency_ms=response.latency_ms,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        context.add_step(step)
        context.scratchpad["critic_satisfied"] = False
        context.scratchpad["final_answer"] = ""
        context.scratchpad["critic_suggestion"] = "Critic 评判失败，建议重试"
        return step

    def _parse_verdict(self, raw: str) -> tuple[str, bool, str, str, str | None]:
        """解析 LLM 输出。

        Returns:
            (thought, satisfied, answer, suggestion, error)
        """
        if not raw or not raw.strip():
            return "", False, "", "", "LLM 返回了空内容"

        cleaned, error = _clean_json_text(raw)
        if cleaned is None:
            return raw[:500], False, "", "", error

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError as e2:
                    return raw[:500], False, "", "", f"JSON 解析失败: {e2}"
            else:
                return raw[:500], False, "", "", f"未找到 JSON 对象: {e}"

        thought = data.get("thought", "")
        satisfied = bool(data.get("satisfied", False))
        answer = data.get("answer", "")
        suggestion = data.get("suggestion", "")

        return thought, satisfied, answer, suggestion, None