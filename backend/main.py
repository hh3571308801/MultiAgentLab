"""FastAPI 应用入口。

启动方式：
    cd MultiAgentLab
    python -m backend.main

或：
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import __version__
from backend.api import router as api_router
from backend.config import settings

# ===== 日志配置 =====
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ===== FastAPI 应用 =====
app = FastAPI(
    title="MultiAgentLab",
    description="可观测、可评测的多 LLM Agent 协作框架",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event() -> None:
    """启动时打印关键配置。"""
    logger.info("=" * 60)
    logger.info("MultiAgentLab v%s 启动", __version__)
    logger.info("LLM Provider: %s | Model: %s", settings.llm_provider, settings.model_name)
    logger.info("Max Rounds: %d | Trajectory Dir: %s", settings.max_rounds, settings.trajectory_dir)
    logger.info("=" * 60)


# CORS：允许前端单独部署（如 Vercel / GitHub Pages）时跨域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(api_router)


# 挂载前端构建产物（frontend/dist）：clone 后无需 Node，一条命令即可访问完整 UI
_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST_DIR), html=True), name="frontend")
else:
    logger.info(
        "frontend/dist not found — UI disabled. "
        "Build it with `cd frontend && npm install && npm run build`, "
        "or use the dev server (`npm run dev`)."
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower(),
    )