"""LLM 客户端封装。

设计要点：
    1. 统一接口：所有 provider（DeepSeek/OpenAI/Qwen）走 OpenAI 兼容协议，一套代码
    2. 自动重试：tenacity 处理网络抖动
    3. 计时 + Token 统计：每次调用返回耗时和 token 消耗，供轨迹记录
    4. Mock 模式：无 API Key 时返回固定响应，方便本地调试
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """单次 LLM 调用的完整响应（包含元数据）。"""

    content: str
    token_in: int
    token_out: int
    latency_ms: int
    model: str
    raw: dict[str, Any] | None = None


class LLMClient:
    """异步 LLM 客户端。

    用法：
        client = LLMClient()
        resp = await client.chat(messages=[{"role": "user", "content": "..."}])
        print(resp.content, resp.token_in, resp.latency_ms)
    """

    def __init__(self) -> None:
        """根据当前 provider 初始化客户端。"""
        self.provider = settings.llm_provider
        self.model = settings.model_name

        if self.provider == "mock":
            self._client: AsyncOpenAI | None = None
            logger.warning("LLM provider = mock，所有调用返回固定响应（仅用于本地调试）")
        else:
            self._client = AsyncOpenAI(
                api_key=settings.api_key,
                base_url=settings.base_url,
                timeout=settings.request_timeout,
            )
            logger.info(
                "LLM client initialized: provider=%s, model=%s",
                self.provider,
                self.model,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """发送对话请求，自动重试 + 计时 + 统计 token。

        Args:
            messages: OpenAI 格式的消息列表 [{"role": ..., "content": ...}, ...]
            temperature: 采样温度，越低越确定
            max_tokens: 单次响应最大 token 数

        Returns:
            LLMResponse: 含内容、token、耗时

        Raises:
            RuntimeError: API 调用失败（已重试 3 次）
        """
        if self.provider == "mock":
            return self._mock_response(messages)

        assert self._client is not None
        start = time.perf_counter()

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.exception("LLM 调用失败: %s", e)
            raise RuntimeError(f"LLM call failed: {e}") from e

        latency_ms = int((time.perf_counter() - start) * 1000)

        # 解析响应
        choice = response.choices[0]
        content = choice.message.content or ""
        usage = response.usage
        token_in = usage.prompt_tokens if usage else 0
        token_out = usage.completion_tokens if usage else 0

        logger.debug(
            "LLM call ok: model=%s, tokens_in=%d, tokens_out=%d, latency=%dms",
            self.model,
            token_in,
            token_out,
            latency_ms,
        )

        return LLMResponse(
            content=content,
            token_in=token_in,
            token_out=token_out,
            latency_ms=latency_ms,
            model=self.model,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    def _mock_response(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Mock 模式：根据 system role 返回固定响应。

        用途：
            - 本地调试，不消耗 API 配额
            - CI 测试
        """
        await_time = 0.1  # 模拟延迟
        # 简化：直接 sleep
        # 注意：这里不能用 await，因为 chat 是 sync 调用的
        # 改为简单 sleep
        time.sleep(await_time)

        system_msg = next(
            (m["content"] for m in messages if m["role"] == "system"),
            "",
        )

        # 根据角色返回固定模板
        if "Planner" in system_msg:
            content = (
                "{\n"
                '  "thought": "我需要把任务分解成子任务",\n'
                '  "plan": [\n'
                '    {"step_id": 1, "subtask": "计算小明花掉的钱", "expected_tool": "calculator"},\n'
                '    {"step_id": 2, "subtask": "用总钱数减去花掉的钱", "expected_tool": "calculator"}\n'
                "  ]\n"
                "}"
            )
        elif "Executor" in system_msg:
            content = (
                "{\n"
                '  "thought": "调用计算器执行当前子任务",\n'
                '  "action": {\n'
                '    "tool_name": "calculator",\n'
                '    "tool_input": "10 - 3"\n'
                "  }\n"
                "}"
            )
        elif "Critic" in system_msg:
            content = (
                "{\n"
                '  "thought": "执行结果正确, 任务完成",\n'
                '  "satisfied": true,\n'
                '  "answer": "答案是 7 元",\n'
                '  "suggestion": ""\n'
                "}"
            )
        else:
            content = "[MOCK] 我是 mock LLM，请配置真实 API Key。"

        return LLMResponse(
            content=content,
            token_in=sum(len(m["content"]) for m in messages) // 4,
            token_out=len(content) // 4,
            latency_ms=int(await_time * 1000),
            model="mock-model",
        )


# 全局单例（按需惰性初始化）
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例（线程不安全但 FastAPI 单线程 async 足够）。"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client