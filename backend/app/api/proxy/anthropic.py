"""
Anthropic 兼容代理接口

提供 Anthropic 风格的 API 代理端点。
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.deps import CurrentApiKey, ProxyServiceDep
from app.common.errors import AppError

router = APIRouter(tags=["Anthropic Proxy"])


@router.post("/v1/messages")
async def messages(
    request: Request,
    api_key: CurrentApiKey,
    proxy_service: ProxyServiceDep,
) -> Any:
    """
    Anthropic Messages 代理接口
    
    将请求转发到配置的上游供应商，仅修改 model 字段。
    """
    # 获取请求体
    body = await request.json()
    
    # 获取请求头
    headers = dict(request.headers)
    
    try:
        # 处理请求
        response, log_info = await proxy_service.process_request(
            api_key_id=api_key.id,
            api_key_name=api_key.key_name,
            path="/v1/messages",
            method="POST",
            headers=headers,
            body=body,
        )
        
        # 返回响应
        if response.is_success:
            return JSONResponse(
                content=response.body,
                status_code=response.status_code,
                headers={
                    "X-Trace-ID": log_info.get("trace_id", ""),
                    "X-Target-Model": log_info.get("target_model", ""),
                    "X-Provider": log_info.get("provider_name", ""),
                },
            )
        else:
            return JSONResponse(
                content=response.body or {"error": {"message": response.error}},
                status_code=response.status_code,
            )
    
    except AppError as e:
        return JSONResponse(
            content=e.to_dict(),
            status_code=e.status_code,
        )
