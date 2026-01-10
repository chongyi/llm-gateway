"""
代理接口模块初始化
"""

from app.api.proxy.openai import router as openai_router
from app.api.proxy.anthropic import router as anthropic_router

__all__ = [
    "openai_router",
    "anthropic_router",
]
