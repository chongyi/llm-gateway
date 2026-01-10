"""
Token 计数器模块

提供不同协议（OpenAI、Anthropic）的 Token 计数实现。
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class TokenCounter(ABC):
    """
    Token 计数器抽象基类
    
    定义 Token 计数的标准接口，由具体实现类提供计算逻辑。
    """
    
    @abstractmethod
    def count_tokens(self, text: str, model: str = "") -> int:
        """
        计算文本的 Token 数量
        
        Args:
            text: 要计算的文本
            model: 模型名称（不同模型可能使用不同的 tokenizer）
        
        Returns:
            int: Token 数量
        """
        pass
    
    @abstractmethod
    def count_messages(self, messages: list[dict[str, Any]], model: str = "") -> int:
        """
        计算消息列表的 Token 数量
        
        Args:
            messages: 消息列表，格式如 [{"role": "user", "content": "Hello"}]
            model: 模型名称
        
        Returns:
            int: Token 数量
        """
        pass


class OpenAITokenCounter(TokenCounter):
    """
    OpenAI Token 计数器
    
    使用 tiktoken 库进行精确的 Token 计数。
    支持 GPT-3.5、GPT-4 等模型。
    """
    
    # 默认使用的编码
    DEFAULT_ENCODING = "cl100k_base"
    
    # 模型到编码的映射
    MODEL_ENCODING_MAP = {
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "text-embedding-ada-002": "cl100k_base",
        "text-davinci-003": "p50k_base",
    }
    
    def __init__(self):
        """初始化计数器"""
        self._encodings: dict[str, Any] = {}
    
    def _get_encoding(self, model: str) -> Any:
        """
        获取模型对应的编码器
        
        Args:
            model: 模型名称
        
        Returns:
            tiktoken 编码器实例
        """
        if not TIKTOKEN_AVAILABLE:
            return None
        
        # 查找模型对应的编码
        encoding_name = self.DEFAULT_ENCODING
        for model_prefix, enc_name in self.MODEL_ENCODING_MAP.items():
            if model.startswith(model_prefix):
                encoding_name = enc_name
                break
        
        # 缓存编码器
        if encoding_name not in self._encodings:
            self._encodings[encoding_name] = tiktoken.get_encoding(encoding_name)
        
        return self._encodings[encoding_name]
    
    def count_tokens(self, text: str, model: str = "") -> int:
        """
        计算文本的 Token 数量
        
        使用 tiktoken 进行精确计算。如果 tiktoken 不可用，
        则使用估算方法（约4个字符一个 token）。
        
        Args:
            text: 要计算的文本
            model: 模型名称
        
        Returns:
            int: Token 数量
        """
        if not text:
            return 0
        
        encoding = self._get_encoding(model)
        if encoding:
            return len(encoding.encode(text))
        
        # 降级估算：平均4个字符一个 token
        return len(text) // 4
    
    def count_messages(self, messages: list[dict[str, Any]], model: str = "") -> int:
        """
        计算消息列表的 Token 数量
        
        按照 OpenAI 的消息格式计算，包含角色和内容的 overhead。
        
        Args:
            messages: 消息列表
            model: 模型名称
        
        Returns:
            int: Token 数量
        """
        if not messages:
            return 0
        
        # 每条消息的 overhead
        tokens_per_message = 4  # <|start|>role<|separator|>content<|end|>
        tokens_per_name = -1  # 如果有 name 字段
        
        total_tokens = 0
        for message in messages:
            total_tokens += tokens_per_message
            for key, value in message.items():
                if isinstance(value, str):
                    total_tokens += self.count_tokens(value, model)
                elif isinstance(value, list):
                    # 处理 content 为数组的情况（多模态）
                    for item in value:
                        if isinstance(item, dict) and "text" in item:
                            total_tokens += self.count_tokens(item["text"], model)
                if key == "name":
                    total_tokens += tokens_per_name
        
        total_tokens += 3  # 每个回复的 priming
        return total_tokens


class AnthropicTokenCounter(TokenCounter):
    """
    Anthropic Token 计数器
    
    Anthropic 使用自己的 tokenizer，这里提供估算实现。
    实际项目中建议集成 Anthropic 的官方 tokenizer。
    """
    
    def count_tokens(self, text: str, model: str = "") -> int:
        """
        计算文本的 Token 数量
        
        使用估算方法，Anthropic 的 tokenizer 与 OpenAI 类似，
        但具体实现可能略有不同。
        
        Args:
            text: 要计算的文本
            model: 模型名称
        
        Returns:
            int: Token 数量（估算值）
        """
        if not text:
            return 0
        
        # 估算：平均4个字符一个 token
        # TODO: 集成 Anthropic 官方 tokenizer 以获得精确计数
        return len(text) // 4
    
    def count_messages(self, messages: list[dict[str, Any]], model: str = "") -> int:
        """
        计算消息列表的 Token 数量
        
        Args:
            messages: 消息列表
            model: 模型名称
        
        Returns:
            int: Token 数量（估算值）
        """
        if not messages:
            return 0
        
        total_tokens = 0
        for message in messages:
            # Anthropic 消息格式
            role = message.get("role", "")
            content = message.get("content", "")
            
            total_tokens += self.count_tokens(role, model)
            
            if isinstance(content, str):
                total_tokens += self.count_tokens(content, model)
            elif isinstance(content, list):
                # 处理 content 为数组的情况
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        total_tokens += self.count_tokens(item["text"], model)
            
            # 消息 overhead
            total_tokens += 4
        
        return total_tokens


def get_token_counter(protocol: str) -> TokenCounter:
    """
    获取指定协议的 Token 计数器
    
    Args:
        protocol: 协议类型，"openai" 或 "anthropic"
    
    Returns:
        TokenCounter: 对应的计数器实例
    """
    if protocol.lower() == "anthropic":
        return AnthropicTokenCounter()
    return OpenAITokenCounter()
