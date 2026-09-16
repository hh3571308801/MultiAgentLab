"""配置加载模块。

负责从环境变量（.env）读取所有配置项，做类型校验和默认值填充。

设计原则：
    1. 单一职责：只负责配置加载，不做任何业务逻辑
    2. 启动时校验：缺失关键配置时立即报错，避免运行时崩溃
    3. 敏感信息隔离：API Key 通过 pydantic 不打印到日志
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用全局配置（单例）。

    所有配置项从环境变量或 .env 文件读取。
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== LLM Provider =====
    llm_provider: Literal["deepseek", "openai", "qwen", "mock"] = "deepseek"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Qwen
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # ===== 运行参数 =====
    max_rounds: int = Field(default=5, ge=1, le=20, description="最大重规划轮数")
    request_timeout: int = Field(default=60, ge=5, le=300, description="单次 LLM 调用超时（秒）")
    log_level: str = "INFO"

    # ===== 存储 =====
    trajectory_dir: str = "./data/trajectories"

    # ===== 派生属性 =====
    @property
    def api_key(self) -> str:
        """根据当前 provider 自动获取对应 API Key。"""
        key = {
            "deepseek": self.deepseek_api_key,
            "openai": self.openai_api_key,
            "qwen": self.qwen_api_key,
            "mock": "",
        }.get(self.llm_provider, "")
        if not key and self.llm_provider != "mock":
            raise ValueError(
                f"LLM_PROVIDER={self.llm_provider} 但未配置对应的 API Key。"
                f"请检查 .env 文件。"
            )
        return key

    @property
    def base_url(self) -> str:
        """根据当前 provider 自动获取对应 base_url。"""
        return {
            "deepseek": self.deepseek_base_url,
            "openai": self.openai_base_url,
            "qwen": self.qwen_base_url,
            "mock": "",
        }[self.llm_provider]

    @property
    def model_name(self) -> str:
        """根据当前 provider 自动获取对应模型名。"""
        return {
            "deepseek": self.deepseek_model,
            "openai": self.openai_model,
            "qwen": self.qwen_model,
            "mock": "mock-model",
        }[self.llm_provider]

    @field_validator("trajectory_dir")
    @classmethod
    def ensure_trajectory_dir(cls, v: str) -> str:
        """确保轨迹目录存在。"""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v


# 全局单例
settings = Settings()