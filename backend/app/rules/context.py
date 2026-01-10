"""
规则上下文模块

定义规则引擎执行时所需的上下文数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TokenUsage:
    """
    Token 使用量数据类
    
    记录请求的 Token 消耗情况。
    """
    
    # 输入 Token 数
    input_tokens: int = 0
    # 输出 Token 数（通常在规则评估时尚未产生）
    output_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        """获取总 Token 数"""
        return self.input_tokens + self.output_tokens


@dataclass
class RuleContext:
    """
    规则引擎上下文
    
    包含规则评估所需的所有输入数据：
    - current_model: 当前请求的模型名
    - headers: 请求头（结构化对象）
    - request_body: 请求体（结构化对象）
    - token_usage: Token 消耗统计
    """
    
    # 当前请求的模型名（requested_model）
    current_model: str
    # 请求头
    headers: dict[str, str] = field(default_factory=dict)
    # 请求体
    request_body: dict[str, Any] = field(default_factory=dict)
    # Token 使用量
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    
    def get_value(self, field_path: str) -> Optional[Any]:
        """
        根据字段路径获取值
        
        支持以下路径格式：
        - "model" -> current_model
        - "headers.x-priority" -> headers["x-priority"]
        - "body.temperature" -> request_body["temperature"]
        - "body.messages[0].role" -> request_body["messages"][0]["role"]
        - "token_usage.input_tokens" -> token_usage.input_tokens
        
        Args:
            field_path: 字段路径
        
        Returns:
            Optional[Any]: 字段值，不存在则返回 None
        """
        if not field_path:
            return None
        
        parts = field_path.split(".")
        root = parts[0].lower()
        
        # 处理根字段
        if root == "model":
            return self.current_model
        elif root == "headers":
            return self._get_nested_value(self.headers, parts[1:])
        elif root == "body":
            return self._get_nested_value(self.request_body, parts[1:])
        elif root == "token_usage":
            return self._get_token_usage_value(parts[1:])
        
        return None
    
    def _get_nested_value(self, obj: Any, path: list[str]) -> Optional[Any]:
        """
        获取嵌套对象的值
        
        支持字典键和数组索引访问。
        
        Args:
            obj: 当前对象
            path: 剩余路径部分
        
        Returns:
            Optional[Any]: 值或 None
        """
        if not path:
            return obj
        
        current = path[0]
        remaining = path[1:]
        
        # 处理数组索引，如 "messages[0]"
        if "[" in current and current.endswith("]"):
            key = current[:current.index("[")]
            index_str = current[current.index("[") + 1:-1]
            
            try:
                index = int(index_str)
                if isinstance(obj, dict) and key in obj:
                    arr = obj[key]
                    if isinstance(arr, list) and 0 <= index < len(arr):
                        return self._get_nested_value(arr[index], remaining)
            except (ValueError, IndexError):
                pass
            return None
        
        # 处理普通键
        if isinstance(obj, dict) and current in obj:
            return self._get_nested_value(obj[current], remaining)
        
        return None
    
    def _get_token_usage_value(self, path: list[str]) -> Optional[Any]:
        """获取 token_usage 的字段值"""
        if not path:
            return self.token_usage
        
        field_name = path[0]
        if field_name == "input_tokens":
            return self.token_usage.input_tokens
        elif field_name == "output_tokens":
            return self.token_usage.output_tokens
        elif field_name == "total_tokens":
            return self.token_usage.total_tokens
        
        return None
