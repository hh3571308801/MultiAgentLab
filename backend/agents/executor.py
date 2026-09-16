"""Executor Agent：负责执行具体子任务，调用工具。

鲁棒性设计同 Planner：
    1. Few-shot prompt
    2. 多种解析策略（处理 markdown / 前缀）
    3. 自动重试（最多 2 次）
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from backend.agents.base import AgentContext, BaseAgent
from backend.agents.planner import _clean_json_text
from backend.tools import get_tool_registry
from backend.trajectory.schema import Action, Step

logger = logging.getLogger(__name__)


# Executor 的系统提示词（v2: few-shot + 强约束）
EXECUTOR_SYSTEM_PROMPT = """你是 MultiAgentLab 框架的 Executor Agent，职责是执行 Planner 分解的子任务，必要时调用工具。

【可用工具】
{tool_descriptions}

【严格输出规则 - 必须遵守】
1. 你的唯一输出必须是合法 JSON，不能包含任何其他文字、解释、Markdown 代码块标记
2. 不要用 ```json 或 ``` 包裹你的输出
3. 不要输出 "以下是 JSON:" 这类前缀
4. 思考过程放在 JSON 的 thought 字段里

【输出格式】
{"thought":"你对当前子任务的分析","action":{"tool_name":"工具名 或 null","tool_input":"工具输入字符串 或 空字符串"}}

【action 规则】
1. 如果子任务需要调用工具，tool_name 必须从【可用工具】列表里选，不要编造
2. 如果子任务不需要工具（如思考、总结、回答），tool_name 设为 null
3. tool_input 必须是字符串

【Few-shot 示例 1 - 需要工具】
子任务："计算 15 - 3 * 2"
你的输出：
{"thought":"用计算器算术","action":{"tool_name":"calculator","tool_input":"15 - 3 * 2"}}

【Few-shot 示例 2 - 不需要工具】
子任务："验证 9 是合理答案"
你的输出：
{"thought":"答案正确，无需工具","action":{"tool_name":null,"tool_input":""}}
"""


class ExecutorAgent(BaseAgent):
    """执行 Agent。"""

    role = "executor"
    system_prompt = EXECUTOR_SYSTEM_PROMPT

    async def act(self, context: AgentContext) -> Step:
        """执行当前子任务，带重试机制。"""
        current_subtask = self._get_current_subtask(context)

        # 构造 user prompt
        user_prompt = (
            f"【用户任务】\n{context.task}\n\n"
            f"【当前子任务】\n{current_subtask}\n\n"
            f"【历史步骤】\n{self._format_history(context.history)}\n\n"
            f"请执行当前子任务，需要工具就调用工具。"
        )

        # 工具列表注入
        tool_descs = self._get_tool_descriptions()
        system_prompt = self.system_prompt.replace("{tool_descriptions}", tool_descs)

        base_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

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

            response = await self.llm.chat(messages, temperature=0.2)
            thought, action, error = self._parse_action(response.content)

            if error is None:
                # 执行工具
                observation: str | None = None
                if action and action.tool_name:
                    observation = self._execute_tool(action.tool_name, action.tool_input)

                # 更新计划进度
                context.scratchpad["plan_index"] = context.scratchpad.get("plan_index", 0) + 1

                step = Step(
                    step_id=len(context.history) + 1,
                    agent_role=self.role,
                    thought=thought,
                    action=action,
                    observation=observation,
                    token_in=response.token_in,
                    token_out=response.token_out,
                    latency_ms=response.latency_ms,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                context.add_step(step)
                return step

            last_error = error
            logger.warning("Executor 解析失败 (attempt %d/2): %s", attempt + 1, error)

        # 兜底：两次都解析失败
        logger.error("Executor 重试 2 次仍无法解析: %s", response.content[:200])
        step = Step(
            step_id=len(context.history) + 1,
            agent_role=self.role,
            thought=f"[解析失败] LLM 输出无法解析。原始输出: {response.content[:300]}",
            action=None,
            observation="⚠️ Executor 输出无法解析，跳过本步骤",
            token_in=response.token_in,
            token_out=response.token_out,
            latency_ms=response.latency_ms,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        context.add_step(step)
        context.scratchpad["plan_index"] = context.scratchpad.get("plan_index", 0) + 1
        return step

    def _get_current_subtask(self, context: AgentContext) -> str:
        """从 Planner 的计划中取出当前要执行的子任务。"""
        plan = context.scratchpad.get("plan", [])
        index = context.scratchpad.get("plan_index", 0)
        if not plan:
            return "（无计划，自由执行当前用户任务）"
        if index >= len(plan):
            return "（所有子任务已完成）"
        return plan[index].get("subtask", "")

    def _parse_action(self, raw: str) -> tuple[str, Action | None, str | None]:
        """从 LLM 输出解析 thought + action。

        Returns:
            (thought, action, error) — error 为 None 表示成功
        """
        if not raw or not raw.strip():
            return "", None, "LLM 返回了空内容"

        cleaned, error = _clean_json_text(raw)
        if cleaned is None:
            return raw[:500], None, error

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError as e2:
                    return raw[:500], None, f"JSON 解析失败: {e2}"
            else:
                return raw[:500], None, f"未找到 JSON 对象: {e}"

        thought = data.get("thought", "")
        action_data = data.get("action", {})

        if not isinstance(action_data, dict):
            return thought, None, f"action 字段不是 dict: {type(action_data).__name__}"

        tool_name = action_data.get("tool_name")
        tool_input = action_data.get("tool_input", "")

        # 处理 null / None / 空字符串 / "null"
        if tool_name is None or tool_name == "null" or tool_name == "":
            return thought, None, None

        return thought, Action(tool_name=tool_name, tool_input=str(tool_input)), None

    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """调用工具并返回结果。"""
        registry = get_tool_registry()
        tool = registry.get(tool_name)
        if tool is None:
            return f"[错误] 未找到工具: {tool_name}（可用工具: {registry.list_tools()}）"
        try:
            return tool(tool_input)
        except Exception as e:
            logger.exception("工具执行失败: %s(%s)", tool_name, tool_input)
            return f"[错误] 工具执行失败: {e}"

    def _get_tool_descriptions(self) -> str:
        """获取所有可用工具的描述。"""
        registry = get_tool_registry()
        if not registry.list_tools():
            return "（暂无可用工具）"
        lines = []
        for name in registry.list_tools():
            tool = registry.get(name)
            assert tool is not None
            lines.append(f"- {name}: {tool.description}")
        return "\n".join(lines)