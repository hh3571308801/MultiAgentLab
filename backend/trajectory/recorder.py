"""轨迹记录器：负责把内存中的 Trajectory 持久化到磁盘。"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from backend.config import settings
from backend.trajectory.schema import Trajectory

logger = logging.getLogger(__name__)


class TrajectoryRecorder:
    """轨迹记录器。

    用法：
        recorder = TrajectoryRecorder()
        traj = recorder.create(task="用户任务")
        # ... 跑 Agent ...
        traj.steps.append(...)
        recorder.save(traj)  # 保存到 ./data/trajectories/{run_id}.json
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.trajectory_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("TrajectoryRecorder 初始化, base_dir=%s", self.base_dir)

    def create(self, task: str) -> Trajectory:
        """创建一条新轨迹（分配 run_id）。"""
        return Trajectory(
            run_id=str(uuid.uuid4()),
            task=task,
        )

    def save(self, trajectory: Trajectory) -> Path:
        """保存轨迹到 JSON 文件。

        Returns:
            保存的文件路径
        """
        trajectory.recompute_totals()
        file_path = self.base_dir / f"{trajectory.run_id}.json"

        # 使用 Pydantic 的 model_dump(mode="json") 把 datetime 序列化为 ISO 字符串
        data = trajectory.model_dump(mode="json")

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(
            "轨迹已保存: %s (steps=%d, total_tokens=%d, total_latency=%dms)",
            file_path.name,
            len(trajectory.steps),
            trajectory.total_tokens,
            trajectory.total_latency_ms,
        )
        return file_path

    def load(self, run_id: str) -> Trajectory:
        """从 JSON 文件加载轨迹。

        Raises:
            FileNotFoundError: 不存在该 run_id
        """
        file_path = self.base_dir / f"{run_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"轨迹不存在: {run_id}")

        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return Trajectory.model_validate(data)

    def list_runs(self) -> list[str]:
        """列出所有已保存的 run_id。"""
        return sorted(p.stem for p in self.base_dir.glob("*.json"))