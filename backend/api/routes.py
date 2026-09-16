"""HTTP API 路由。

端点：
    POST /api/v1/run          - 执行一个新任务
    GET  /api/v1/trajectories - 列出所有 run_id
    GET  /api/v1/trajectories/{run_id} - 获取某次运行的完整轨迹
    GET  /api/v1/health       - 健康检查
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.orchestrator import Orchestrator
from backend.trajectory.recorder import TrajectoryRecorder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["MultiAgentLab"])


# ===== Request / Response Models =====


class RunRequest(BaseModel):
    """运行任务的请求体。"""

    task: str = Field(..., min_length=1, max_length=2000, description="用户任务")


class RunResponse(BaseModel):
    """运行响应的简要信息。"""

    run_id: str
    task: str
    status: str
    rounds_used: int
    total_steps: int
    total_tokens: int
    total_latency_ms: int
    final_answer: str


# ===== Endpoints =====


@router.post("/run", response_model=RunResponse, summary="运行一个多 Agent 任务")
async def run_task(req: RunRequest) -> RunResponse:
    """运行任务，返回 run_id 和摘要。完整轨迹通过 GET /trajectories/{run_id} 获取。"""
    try:
        orchestrator = Orchestrator()
        trajectory = await orchestrator.run(req.task)
        return RunResponse(
            run_id=trajectory.run_id,
            task=trajectory.task,
            status=trajectory.status.value,
            rounds_used=trajectory.metadata.get("rounds_used", 0),
            total_steps=len(trajectory.steps),
            total_tokens=trajectory.total_tokens,
            total_latency_ms=trajectory.total_latency_ms,
            final_answer=trajectory.final_answer,
        )
    except Exception as e:
        logger.exception("运行任务失败")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/trajectories", summary="列出所有已保存的轨迹 run_id")
async def list_trajectories() -> dict:
    recorder = TrajectoryRecorder()
    return {"run_ids": recorder.list_runs(), "count": len(recorder.list_runs())}


@router.get("/trajectories/{run_id}", summary="获取某次运行的完整轨迹")
async def get_trajectory(run_id: str) -> dict:
    recorder = TrajectoryRecorder()
    try:
        trajectory = recorder.load(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trajectory not found: {run_id}")
    return trajectory.model_dump(mode="json")


@router.get("/health", summary="健康检查")
async def health() -> dict:
    from backend.config import settings

    return {
        "status": "ok",
        "version": "0.1.0",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.model_name,
        "max_rounds": settings.max_rounds,
    }