"""一键跑一次真实 LLM 任务（无需 pytest）。

用法：
    # 1. 配置 .env
    cp .env.example .env
    # 编辑 .env，填入 DEEPSEEK_API_KEY，把 LLM_PROVIDER 改为 deepseek

    # 2. 跑这个脚本
    python scripts/run_real_demo.py

    # 或者自定义任务
    python scripts/run_real_demo.py "今天西安的天气如何？"

输出：
    - 终端打印漂亮的步骤报告
    - 完整轨迹 JSON 保存到 ./data/trajectories/{run_id}.json
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 让脚本能找到 backend 包
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.orchestrator import Orchestrator  # noqa: E402


DEFAULT_TASK = "小红有 15 元钱，买了 3 支铅笔每支 2 元，还剩多少？"


async def main(task: str) -> None:
    """跑一次任务并打印报告。"""
    print()
    print("=" * 64)
    print(f"🚀 启动真实 LLM 任务")
    print("=" * 64)
    print(f"任务: {task}")
    print()

    orchestrator = Orchestrator()
    trajectory = await orchestrator.run(task)

    _print_report(trajectory)

    # 保存路径提示
    saved_path = PROJECT_ROOT / "data" / "trajectories" / f"{trajectory.run_id}.json"
    print(f"\n📁 完整轨迹已保存: {saved_path}")

    # 提示用户下一步
    print("\n" + "=" * 64)
    print("💡 下一步")
    print("=" * 64)
    print(f"  1. 查看完整 JSON: cat {saved_path}")
    print(f"  2. 跑更多任务: python scripts/run_real_demo.py \"你的任务\"")
    print(f"  3. 启动 API 服务: python -m backend.main")
    print(f"  4. 浏览器调试: 打开 http://localhost:8000/docs")
    print()


def _print_report(traj) -> None:
    """打印漂亮的运行报告（emoji 版本）。"""
    print("\n" + "=" * 64)
    print("✅ 运行完成")
    print("=" * 64)
    print(f"Run ID:       {traj.run_id}")
    print(f"任务:         {traj.task}")
    print(f"最终答案:     {traj.final_answer}")
    print(f"状态:         {traj.status.value}")
    print(f"总步数:       {len(traj.steps)}")
    print(f"总 Token:     {traj.total_tokens}")
    print(f"总耗时:       {traj.total_latency_ms}ms")
    print(f"使用模型:     {traj.metadata.get('llm_model', 'unknown')}")
    print(f"LLM Provider: {traj.metadata.get('llm_provider', 'unknown')}")
    print()
    print("─── 步骤详情 ───")

    icons = {"planner": "🎯", "executor": "⚙️ ", "critic": "🔍"}
    for s in traj.steps:
        icon = icons.get(s.agent_role, "•")
        print(f"\n{icon} [{s.step_id}] {s.agent_role}")
        print(f"   💭 {s.thought}")
        if s.action:
            print(f"   🔧 {s.action.tool_name}({s.action.tool_input})")
        if s.observation:
            print(f"   📥 {s.observation}")
        print(
            f"   📊 tokens={s.token_in}+{s.token_out} | "
            f"latency={s.latency_ms}ms"
        )


if __name__ == "__main__":
    # 支持命令行参数自定义任务
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = DEFAULT_TASK

    try:
        asyncio.run(main(task))
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行失败: {e}", file=sys.stderr)
        print("\n💡 可能的原因：")
        print("   1. .env 文件没填 API Key（查看 LLM_PROVIDER 和 DEEPSEEK_API_KEY）")
        print("   2. 网络问题，无法访问 DeepSeek API")
        print("   3. API Key 无效或余额不足")
        print("\n详见 docs/HOW_TO_REPLACE_MOCK.md")
        sys.exit(1)