"""
请求/响应领域模型

定义代理请求和响应相关的数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ProxyRequest:
    """
    代理请求数据类
    
    封装客户端发来的请求信息。
    """
    
    # 请求路径（如 /v1/chat/completions）
    path: str
    # HTTP 方法
    method: str
    # 请求头
    headers: dict[str, str]
    # 请求体
    body: dict[str, Any]
    # 协议类型（openai / anthropic）
    protocol: str
    # API Key ID
    api_key_id: int
    # API Key 名称
    api_key_name: str
    # 追踪 ID
    trace_id: str
    # 请求时间
    request_time: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def requested_model(self) -> Optional[str]:
        """获取请求的模型名"""
        return self.body.get("model")
    
    @property
    def is_stream(self) -> bool:
        """是否是流式请求"""
        return self.body.get("stream", False)


@dataclass
class ProxyResponse:
    """
    代理响应数据类
    
    封装转发后的响应信息。
    """
    
    # HTTP 状态码
    status_code: int
    # 响应头
    headers: dict[str, str]
    # 响应体（非流式）
    body: Any
    # 目标模型名
    target_model: str
    # 供应商 ID
    provider_id: int
    # 供应商名称
    provider_name: str
    # 重试次数
    retry_count: int = 0
    # 首字节延迟（毫秒）
    first_byte_delay_ms: Optional[int] = None
    # 总耗时（毫秒）
    total_time_ms: Optional[int] = None
    # 输入 Token 数
    input_tokens: Optional[int] = None
    # 输出 Token 数
    output_tokens: Optional[int] = None
    # 错误信息
    error_info: Optional[str] = None
    # 是否成功
    success: bool = True
    
    @property
    def is_error(self) -> bool:
        """是否是错误响应"""
        return not self.success or self.status_code >= 400


@dataclass
class CandidateProvider:
    """
    候选供应商数据类
    
    规则引擎匹配后输出的候选供应商信息。
    """
    
    # 供应商 ID
    provider_id: int
    # 供应商名称
    provider_name: str
    # 供应商基础 URL
    base_url: str
    # 供应商协议
    protocol: str
    # 供应商 API Key
    api_key: Optional[str]
    # 目标模型名（该供应商对应的实际模型）
    target_model: str
    # 优先级
    priority: int = 0
    # 权重
    weight: int = 1
