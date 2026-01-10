"""
HTTP 客户端封装模块

提供统一的异步 HTTP 客户端，用于与上游供应商通信。
"""

from typing import Any, AsyncGenerator, Optional

import httpx

from app.config import get_settings


class HttpClient:
    """
    异步 HTTP 客户端封装
    
    封装 httpx.AsyncClient，提供统一的请求方法和超时配置。
    支持普通请求和流式请求。
    """
    
    def __init__(
        self,
        base_url: str = "",
        timeout: Optional[int] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        """
        初始化 HTTP 客户端
        
        Args:
            base_url: 基础 URL
            timeout: 请求超时时间（秒），默认使用配置
            headers: 默认请求头
        """
        settings = get_settings()
        self.base_url = base_url
        self.timeout = timeout or settings.HTTP_TIMEOUT
        self.default_headers = headers or {}
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        获取或创建 HTTP 客户端实例
        
        Returns:
            httpx.AsyncClient: HTTP 客户端实例
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=self.default_headers,
            )
        return self._client
    
    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法（GET, POST 等）
            url: 请求 URL（相对于 base_url）
            headers: 请求头
            json: JSON 请求体
            **kwargs: 其他 httpx 参数
        
        Returns:
            httpx.Response: HTTP 响应
        """
        client = await self._get_client()
        return await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            **kwargs,
        )
    
    async def post(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        发送 POST 请求
        
        Args:
            url: 请求 URL
            headers: 请求头
            json: JSON 请求体
            **kwargs: 其他参数
        
        Returns:
            httpx.Response: HTTP 响应
        """
        return await self.request("POST", url, headers=headers, json=json, **kwargs)
    
    async def stream_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[bytes, None]:
        """
        发送流式请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            headers: 请求头
            json: JSON 请求体
            **kwargs: 其他参数
        
        Yields:
            bytes: 响应数据块
        """
        client = await self._get_client()
        async with client.stream(
            method=method,
            url=url,
            headers=headers,
            json=json,
            **kwargs,
        ) as response:
            async for chunk in response.aiter_bytes():
                yield chunk


async def create_client(
    base_url: str,
    api_key: Optional[str] = None,
    timeout: Optional[int] = None,
) -> HttpClient:
    """
    创建配置好的 HTTP 客户端
    
    Args:
        base_url: 基础 URL
        api_key: API Key（用于 Authorization 头）
        timeout: 超时时间
    
    Returns:
        HttpClient: 配置好的客户端实例
    """
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    return HttpClient(base_url=base_url, timeout=timeout, headers=headers)
