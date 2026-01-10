"""
OpenAI 兼容代理接口

提供 OpenAI 风格的 API 代理端点。
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import CurrentApiKey, ProxyServiceDep
from app.common.errors import AppError

router = APIRouter(tags=["OpenAI Proxy"])


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    api_key: CurrentApiKey,
    proxy_service: ProxyServiceDep,
) -> Any:
    """
    OpenAI Chat Completions 代理接口
    
    将请求转发到配置的上游供应商，仅修改 model 字段。
    支持普通请求和流式请求。
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
            path="/v1/chat/completions",
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


@router.post("/v1/completions")
async def completions(
    request: Request,
    api_key: CurrentApiKey,
    proxy_service: ProxyServiceDep,
) -> Any:
    """
    OpenAI Text Completions 代理接口
    """
    body = await request.json()
    headers = dict(request.headers)
    
    try:
        response, log_info = await proxy_service.process_request(
            api_key_id=api_key.id,
            api_key_name=api_key.key_name,
            path="/v1/completions",
            method="POST",
            headers=headers,
            body=body,
        )
        
        if response.is_success:
            return JSONResponse(
                content=response.body,
                status_code=response.status_code,
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


@router.post("/v1/embeddings")
async def embeddings(
    request: Request,
    api_key: CurrentApiKey,
    proxy_service: ProxyServiceDep,
) -> Any:
    """
    OpenAI Embeddings 代理接口
    """
    body = await request.json()
    headers = dict(request.headers)
    
    try:
        response, log_info = await proxy_service.process_request(
            api_key_id=api_key.id,
            api_key_name=api_key.key_name,
            path="/v1/embeddings",
            method="POST",
            headers=headers,
            body=body,
        )
        
        if response.is_success:
            return JSONResponse(
                content=response.body,
                status_code=response.status_code,
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
