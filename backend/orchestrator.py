"""多 Agent 调度器（核心）。

调度流程：
    1. Planner 分解任务
    2. Executor 依次执行子任务
    3. Critic 评判结果
    4. 不满意 → REPLAN；满意或达到最大轮数 → END

最大轮数由 settings.max_rounds 控制，默认 5。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.agents import CriticAgent, ExecutorAgent, PlannerAgent
from backend.agents.base import AgentContext
from backend.config import settings
from backend.llm.client import get_llm_client
from backend.trajectory.recorder import TrajectoryRecorder
from backend.trajectory.schema import RunStatus, Trajectory

logger = logging.getLogger(__name__)


class Orchestrator:
    """多 Agent 调度器。"""

    def __init__(self) -> None:
        llm = get_llm_client()
        self.planner = PlannerAgent(llm)
        self.executor = ExecutorAgent(llm)
        self.critic = CriticAgent(llm)
        self.recorder = TrajectoryRecorder()
        self.max_rounds = settings.max_rounds

    async def run(self, task: str) -> Trajectory:
        """执行一个任务，返回完整轨迹。

        Args:
            task: 用户任务字符串

        Returns:
            Trajectory: 完整运行轨迹（含所有步骤）
        """
        logger.info("=" * 60)
        logger.info("开始运行任务: %s", task[:100])
        logger.info("=" * 60)

        trajectory = self.recorder.create(task)
        context = AgentContext(task=task)

        status = RunStatus.SUCCESS
        final_answer = ""
        try:
            # 1. 规划
            await self.planner.act(context)

            # 2. 多轮执行 + 评判
            for round_idx in range(1, self.max_rounds + 1):
                context.round = round_idx
                logger.info("---- 第 %d 轮 ----", round_idx)

                # 执行所有子任务
                plan = context.scratchpad.get("plan", [])
                plan_index = context.scratchpad.get("plan_index", 0)

                # 如果 plan 为空（Planner 解析失败），给 Executor 一次机会
                end_index = len(plan) if plan else 1
                while context.scratchpad.get("plan_index", 0) < end_index:
                    await self.executor.act(context)

                # 评判
                await self.critic.act(context)
                satisfied = context.scratchpad.get("critic_satisfied", False)
                final_answer = context.scratchpad.get("final_answer", "")

                if satisfied:
                    logger.info("Critic 满意, 任务完成")
                    status = RunStatus.SUCCESS
                    break

                if round_idx < self.max_rounds:
                    logger.info("Critic 不满意, 重新规划")
                    # 重置 Executor 进度，让 Planner 重新规划
                    context.scratchpad["plan_index"] = 0
                    await self.planner.act(context)
                else:
                    logger.warning("达到最大轮数, 强制结束")
                    status = RunStatus.MAX_ROUNDS_REACHED

        except Exception as e:
            logger.exception("运行异常: %s", e)
            status = RunStatus.FAILED
            final_answer = f"[ERROR] {e}"

        # 3. 填充实尾字段
        trajectory.steps = context.history
        trajectory.final_answer = final_answer
        trajectory.status = status
        trajectory.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        trajectory.metadata = {
            "rounds_used": context.round,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.model_name,
        }

        # 4. 保存
        self.recorder.save(trajectory)

        logger.info(
            "任务结束: status=%s, total_steps=%d, total_tokens=%d",
            status.value,
            len(trajectory.steps),
            trajectory.total_tokens,
        )
        return trajectory