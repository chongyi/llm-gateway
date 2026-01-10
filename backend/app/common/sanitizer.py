"""
数据脱敏模块

对敏感信息（如 authorization 头）进行脱敏处理，
确保日志记录不包含明文敏感数据。
"""

import re
from typing import Any


def sanitize_authorization(value: str) -> str:
    """
    脱敏 authorization 字段值
    
    将 API Key 等敏感信息进行掩码处理，保留前缀和部分字符用于识别。
    
    Args:
        value: 原始 authorization 值，如 "Bearer sk-xxxxxxxxxxxx"
    
    Returns:
        str: 脱敏后的值，如 "Bearer sk-***...***"
    
    Examples:
        >>> sanitize_authorization("Bearer sk-1234567890abcdef")
        'Bearer sk-12***...***ef'
        >>> sanitize_authorization("lgw-abcdefghijklmnop")
        'lgw-ab***...***op'
    """
    if not value:
        return value
    
    # 处理 Bearer 前缀
    prefix = ""
    token = value
    if value.lower().startswith("bearer "):
        prefix = "Bearer "
        token = value[7:]
    
    # 如果 token 太短，直接返回掩码
    if len(token) <= 8:
        return f"{prefix}***"
    
    # 保留前4个字符和后2个字符，中间用掩码替换
    return f"{prefix}{token[:4]}***...***{token[-2:]}"


def sanitize_headers(headers: dict[str, Any]) -> dict[str, Any]:
    """
    脱敏请求头
    
    对请求头中的敏感字段进行脱敏处理，目前处理以下字段：
    - authorization
    - x-api-key
    - api-key
    
    Args:
        headers: 原始请求头字典
    
    Returns:
        dict: 脱敏后的请求头字典（新字典，不修改原始数据）
    
    Examples:
        >>> headers = {"authorization": "Bearer sk-xxx", "content-type": "application/json"}
        >>> sanitize_headers(headers)
        {'authorization': 'Bearer sk-***...***', 'content-type': 'application/json'}
    """
    if not headers:
        return {}
    
    # 需要脱敏的字段名（小写）
    sensitive_fields = {"authorization", "x-api-key", "api-key"}
    
    # 创建新字典，避免修改原始数据
    sanitized = {}
    for key, value in headers.items():
        if key.lower() in sensitive_fields and isinstance(value, str):
            sanitized[key] = sanitize_authorization(value)
        else:
            sanitized[key] = value
    
    return sanitized


def sanitize_api_key_display(key_value: str) -> str:
    """
    脱敏 API Key 显示
    
    用于列表展示时的 API Key 脱敏。
    
    Args:
        key_value: 完整的 API Key 值
    
    Returns:
        str: 脱敏后的显示值
    
    Examples:
        >>> sanitize_api_key_display("lgw-abcdefghijklmnopqrstuvwxyz")
        'lgw-abcd***...***yz'
    """
    return sanitize_authorization(key_value)
