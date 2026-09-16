"""轨迹模块：数据模型 + 记录器。

核心职责：
    1. 定义轨迹的 Pydantic Schema（兼容 Shellloop 格式）
    2. 提供轨迹写入文件、读取文件的工具
"""

from .schema import Action, Step, AgentTrace, Trajectory, RunStatus
from .recorder import TrajectoryRecorder

__all__ = [
    "Action",
    "Step",
    "AgentTrace",
    "Trajectory",
    "RunStatus",
    "TrajectoryRecorder",
]