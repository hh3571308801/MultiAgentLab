"""Planner Agent：负责任务分解。

输入：用户任务 + 历史步骤
输出：分解后的子任务列表（用 JSON 格式）

鲁棒性设计：
    1. Few-shot prompt：给 LLM 一个完整示例，模仿输出格式
    2. 多种解析策略：直接 / 提取 {} / 去除 markdown 代码块 / 处理前缀
    3. 自动重试：解析失败时追加 hint 再试一次
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from backend.agents.base import AgentContext, BaseAgent
from backend.trajectory.schema import Step

logger = logging.getLogger(__name__)


# Planner 的系统提示词（v2: few-shot + 强约束）
PLANNER_SYSTEM_PROMPT = """你是 MultiAgentLab 框架的 Planner Agent，职责是把用户任务分解成可执行的子任务列表。

【严格输出规则 - 必须遵守】
1. 你的唯一输出必须是合法 JSON，不能包含任何其他文字、解释、Markdown 代码块标记
2. 不要用 ```json 或 ``` 包裹你的输出
3. 不要输出 "以下是 JSON:" 这类前缀
4. 如果需要思考，把思考内容放在 JSON 的 thought 字段里

【输出格式】
{
    "thought": "（你对任务的理解和分解思路）",
    "plan": [
        {"step_id": 1, "subtask": "（具体可执行的子任务1）", "expected_tool": "calculator 或 search 或 none"},
        {"step_id": 2, "subtask": "（具体可执行的子任务2）", "expected_tool": "..."}
    ]
}

【Few-shot 示例】
输入任务："小明有 10 元，花了 3 元，还剩多少？"
你的输出：
{"thought":"这是一道两步减法题，先算花掉的钱再算剩余","plan":[{"step_id":1,"subtask":"计算总钱数减去花掉的钱","expected_tool":"calculator"},{"step_id":2,"subtask":"验证答案是否合理","expected_tool":"none"}]}

【plan 规则】
1. plan 至少 1 个子任务，最多 5 个
2. 每个子任务要明确、可由单一工具完成
3. 不需要工具时 expected_tool 设为 "none"
4. 子任务按执行顺序排列，step_id 从 1 开始递增
"""


class PlannerAgent(BaseAgent):
    """任务规划 Agent。"""

    role = "planner"
    system_prompt = PLANNER_SYSTEM_PROMPT

    async def act(self, context: AgentContext) -> Step:
        """根据上下文产出规划步骤。

        带重试：解析失败时追加 hint 再调一次。
        """
        messages = self._build_messages(context)
        last_error: str | None = None

        for attempt in range(2):  # 最多 2 次：原请求 + 1 次重试
            if attempt == 1 and last_error:
                # 重试时追加错误提示
                messages = self._build_messages(context) + [
                    {
                        "role": "user",
                        "content": (
                            f"⚠️ 你上一次的输出无法解析为合法 JSON。\n"
                            f"错误信息：{last_error}\n"
                            f"请严格按格式输出纯 JSON，不要加任何额外文字或 markdown。"
                        ),
                    }
                ]

            response = await self.llm.chat(messages, temperature=0.2)
            thought, plan, error = self._parse_plan(response.content)

            if error is None:
                # 解析成功，构造 Step
                context.scratchpad["plan"] = plan
                context.scratchpad["plan_index"] = 0

                step = Step(
                    step_id=len(context.history) + 1,
                    agent_role=self.role,
                    thought=thought,
                    action=None,
                    observation=f"生成计划，共 {len(plan)} 个子任务",
                    token_in=response.token_in,
                    token_out=response.token_out,
                    latency_ms=response.latency_ms,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                context.add_step(step)
                return step

            last_error = error
            logger.warning(
                "Planner 解析失败 (attempt %d/2): %s", attempt + 1, error
            )

        # 两次都失败：构造 fallback Step（plan 为空，让 Executor 自由执行）
        logger.error("Planner 重试 2 次仍无法解析: %s", response.content[:200])
        step = Step(
            step_id=len(context.history) + 1,
            agent_role=self.role,
            thought=f"[解析失败] LLM 输出无法解析为 JSON。原始输出: {response.content[:300]}",
            action=None,
            observation="⚠️ Planner 输出无法解析，将以自由模式执行",
            token_in=response.token_in,
            token_out=response.token_out,
            latency_ms=response.latency_ms,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        context.add_step(step)
        context.scratchpad["plan"] = []
        context.scratchpad["plan_index"] = 0
        return step

    def _parse_plan(self, raw: str) -> tuple[str, list[dict], str | None]:
        """从 LLM 输出解析计划。

        Returns:
            (thought, plan, error) — error 为 None 表示成功

        容错策略（按优先级尝试）：
            1. 直接 json.loads
            2. 去除 markdown 代码块包裹（```json ... ```）
            3. 去除 "JSON:" 等前缀
            4. 正则提取第一个 {...} 块
            5. 全部失败返回原始文本 + 错误信息
        """
        if not raw or not raw.strip():
            return "", [], "LLM 返回了空内容"

        cleaned, error = _clean_json_text(raw)
        if cleaned is None:
            return raw[:500], [], error

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            # 最后尝试：提取第一个 {...} 块
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError as e2:
                    return raw[:500], [], f"JSON 解析失败: {e2}"
            else:
                return raw[:500], [], f"未找到 JSON 对象: {e}"

        thought = data.get("thought", "")
        plan = data.get("plan", [])

        # 校验 plan 是 list
        if not isinstance(plan, list):
            return thought, [], f"plan 字段不是 list: {type(plan).__name__}"

        # 校验每个子任务至少有 subtask 字段
        for i, item in enumerate(plan):
            if not isinstance(item, dict):
                return thought, [], f"plan[{i}] 不是 dict"
            if "subtask" not in item:
                return thought, [], f"plan[{i}] 缺少 subtask 字段"

        return thought, plan, None


def _clean_json_text(raw: str) -> tuple[str | None, str | None]:
    """清理 LLM 输出的常见"杂质"。

    处理：
        1. ```json ... ``` 代码块
        2. ``` ... ``` 普通代码块
        3. "JSON:" / "json:" / "输出：" 等前缀
        4. 首尾空白

    Returns:
        (cleaned_text, error) — cleaned 为 None 表示无法清理
    """
    text = raw.strip()

    # 处理 markdown 代码块
    if text.startswith("```"):
        # 提取代码块内容（去掉第一行的 ```json 和最后一行的 ```）
        match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if match:
            return match.group(1).strip(), None
        # 代码块标记不完整，尝试去掉首尾的 ```
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        return text.strip(), None

    # 处理 "JSON:" / "json:" / "输出：" / "以下是 JSON：" 等前缀
    prefix_pattern = r"^(?:以下是\s*JSON|以下为\s*JSON|JSON\s*输出|JSON\s*输出|输出|Result|Answer|JSON|json)\s*[:：]\s*"
    if re.match(prefix_pattern, text):
        text = re.sub(prefix_pattern, "", text, count=1)

    return text.strip(), None