"""真实 DeepSeek/OpenAI 集成测试（默认 pytest 跳过）。

跑法：
    LLM_PROVIDER=deepseek python -m pytest tests/test_real_deepseek.py -v -m real_llm

要求：
    .env 文件里 DEEPSEEK_API_KEY 已正确填入

注意：
    此测试会**真实消耗 API token**，请确保账户有余额。
    pytest.ini 默认设置 addopts=-m "not real_llm"，所以普通 `pytest` 不会跑这些测试。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# 让 pytest 能找到 backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 模块级 marker：所有测试默认标记为 real_llm
pytestmark = pytest.mark.real_llm


@pytest.fixture(autouse=True)
def skip_if_not_configured():
    """如果 LLM_PROVIDER=mock 或没填真实 API key，自动跳过。

    注意：不通过 settings.api_key property 检查，因为 provider 配置错误时它会抛 ValueError。
    这里直接读取对应字段。
    """
    from backend.config import settings

    if settings.llm_provider == "mock":
        pytest.skip(
            "当前 LLM_PROVIDER=mock。跑真实 LLM 请设置 LLM_PROVIDER=deepseek/openai/qwen"
        )

    # 直接读取字段（避免触发 api_key property 的校验）
    key_map = {
        "deepseek": settings.deepseek_api_key,
        "openai": settings.openai_api_key,
        "qwen": settings.qwen_api_key,
    }
    actual_key = key_map.get(settings.llm_provider, "")
    if not actual_key:
        pytest.skip(
            f"LLM_PROVIDER={settings.llm_provider} 但未配置对应的 API Key。"
            f"请在 .env 里填 {settings.llm_provider.upper()}_API_KEY"
        )


@pytest.mark.asyncio
async def test_real_deepseek_math_problem(capsys):
    """跑一个数学问题，验证端到端流程。"""
    from backend.orchestrator import Orchestrator

    task = "小红有 15 元钱，买了 3 支铅笔每支 2 元，还剩多少？"
    orchestrator = Orchestrator()
    trajectory = await orchestrator.run(task)

    # 基本字段校验
    assert trajectory.run_id
    assert trajectory.task == task
    assert trajectory.status.value in ("success", "max_rounds_reached")
    assert len(trajectory.steps) >= 3  # 至少 Planner + Executor + Critic

    # 三个角色必须出现
    roles = {s.agent_role for s in trajectory.steps}
    assert "planner" in roles, "Planner 未执行"
    assert "executor" in roles, "Executor 未执行"
    assert "critic" in roles, "Critic 未执行"

    # 必须有最终答案
    assert trajectory.final_answer, "final_answer 为空"
    assert len(trajectory.final_answer) > 0

    # 真实 LLM 一定有 token 消耗
    assert trajectory.total_tokens > 0, "total_tokens 为 0，说明没真的调 LLM"

    # 用 capsys 抓 print 输出，断言里有报告
    with capsys.disabled():
        _print_report(trajectory)


def _print_report(traj) -> None:
    """打印漂亮的运行报告。"""
    print("\n" + "=" * 64)
    print(f"✅ 真实 {traj.metadata.get('llm_provider', 'LLM')} 集成测试通过")
    print("=" * 64)
    print(f"任务: {traj.task}")
    print(f"最终答案: {traj.final_answer}")
    print(f"总步数: {len(traj.steps)}")
    print(f"总 Token: {traj.total_tokens}")
    print(f"总耗时: {traj.total_latency_ms}ms")
    print(f"使用模型: {traj.metadata.get('llm_model', 'unknown')}")
    print(f"状态: {traj.status.value}")
    print("=" * 64)
    print("\n步骤详情:")

    icons = {"planner": "🎯", "executor": "⚙️", "critic": "🔍"}
    for s in traj.steps:
        icon = icons.get(s.agent_role, "•")
        print(f"\n{icon} [{s.step_id}] {s.agent_role}")
        print(f"   💭 {s.thought[:200]}")
        if s.action:
            print(f"   🔧 {s.action.tool_name}({s.action.tool_input})")
        if s.observation:
            print(f"   📥 {s.observation[:200]}")
        print(
            f"   📊 tokens={s.token_in}+{s.token_out} | "
            f"latency={s.latency_ms}ms"
        )


if __name__ == "__main__":
    # 直接用 python 跑也可以
    pytest.main([__file__, "-v", "-m", "real_llm", "-s"])