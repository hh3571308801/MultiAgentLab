"""冒烟测试（无需 API Key，使用 mock 模式）。

测试范围：
    1. 计算器工具正确性
    2. 轨迹数据模型序列化
    3. TrajectoryRecorder 创建/保存/读取
    4. Mock 模式下 Orchestrator 跑通完整流程
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# 强制使用 mock 模式（无需 API Key）
os.environ["LLM_PROVIDER"] = "mock"

# 让 pytest 能找到 backend 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_calculator_basic():
    """测试基础计算。"""
    from backend.tools import calculator

    assert calculator("2 + 3") == "5"
    assert calculator("10 - 4") == "6"
    assert calculator("3 * 4") == "12"
    assert calculator("15 / 3") == "5.0"
    assert calculator("2 ** 10") == "1024"
    assert calculator("sqrt(16)") == "4.0"
    assert calculator("pi * 2")[:5] == "6.283"


def test_calculator_safety():
    """测试安全限制（不应执行任意代码）。"""
    from backend.tools import calculator

    result = calculator("__import__('os').system('echo hacked')")
    assert "计算错误" in result or "不支持" in result


def test_trajectory_serialization():
    """测试轨迹数据模型。"""
    from backend.trajectory.schema import Action, Step, Trajectory, RunStatus

    traj = Trajectory(run_id="test-123", task="测试任务")
    step = Step(
        step_id=1,
        agent_role="planner",
        thought="分解任务",
        action=Action(tool_name="calculator", tool_input="2+3"),
        observation="5",
        token_in=10,
        token_out=5,
        latency_ms=100,
    )
    traj.steps.append(step)
    traj.status = RunStatus.SUCCESS
    traj.final_answer = "答案是 5"
    traj.recompute_totals()

    assert traj.total_tokens == 15
    assert traj.total_latency_ms == 100

    # 序列化 + 反序列化
    data = traj.model_dump(mode="json")
    traj2 = Trajectory.model_validate(data)
    assert traj2.run_id == "test-123"
    assert len(traj2.steps) == 1
    assert traj2.steps[0].action.tool_name == "calculator"


def test_recorder_roundtrip():
    """测试轨迹记录器写入 + 读取。"""
    from backend.trajectory.recorder import TrajectoryRecorder
    from backend.trajectory.schema import Step, Trajectory, RunStatus

    tmp_dir = tempfile.mkdtemp()
    try:
        recorder = TrajectoryRecorder(base_dir=tmp_dir)
        traj = recorder.create(task="测试任务")
        traj.steps.append(
            Step(
                step_id=1,
                agent_role="planner",
                thought="x",
            )
        )
        traj.status = RunStatus.SUCCESS
        saved_path = recorder.save(traj)

        assert saved_path.exists()

        # 读取
        loaded = recorder.load(traj.run_id)
        assert loaded.run_id == traj.run_id
        assert loaded.task == "测试任务"
        assert len(loaded.steps) == 1

        # 列出
        runs = recorder.list_runs()
        assert traj.run_id in runs
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_orchestrator_mock():
    """测试 Orchestrator 在 mock 模式下能跑通。"""
    from backend.orchestrator import Orchestrator
    from backend.trajectory.recorder import TrajectoryRecorder

    # 用临时目录
    tmp_dir = tempfile.mkdtemp()
    os.environ["TRAJECTORY_DIR"] = tmp_dir

    try:
        # 重新加载 config 模块
        import importlib
        from backend import config as cfg
        importlib.reload(cfg)

        orchestrator = Orchestrator()
        trajectory = await orchestrator.run("小明有 10 元，花了 3 元，还剩多少？")

        # 验证基本字段
        assert trajectory.run_id
        assert trajectory.task == "小明有 10 元，花了 3 元，还剩多少？"
        assert len(trajectory.steps) >= 3  # 至少 Planner + Executor + Critic
        assert any(s.agent_role == "planner" for s in trajectory.steps)
        assert any(s.agent_role == "executor" for s in trajectory.steps)
        assert any(s.agent_role == "critic" for s in trajectory.steps)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])