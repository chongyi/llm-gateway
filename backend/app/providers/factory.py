"""
供应商客户端工厂模块

根据协议类型创建对应的供应商客户端。
"""

from app.providers.base import ProviderClient
from app.providers.openai_client import OpenAIClient
from app.providers.anthropic_client import AnthropicClient


# 客户端缓存
_clients: dict[str, ProviderClient] = {}


def get_provider_client(protocol: str) -> ProviderClient:
    """
    获取指定协议的供应商客户端
    
    使用缓存避免重复创建客户端实例。
    
    Args:
        protocol: 协议类型，"openai" 或 "anthropic"
    
    Returns:
        ProviderClient: 对应的客户端实例
    
    Raises:
        ValueError: 不支持的协议类型
    """
    protocol = protocol.lower()
    
    if protocol not in _clients:
        if protocol == "openai":
            _clients[protocol] = OpenAIClient()
        elif protocol == "anthropic":
            _clients[protocol] = AnthropicClient()
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    return _clients[protocol]
