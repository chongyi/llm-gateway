"""
重试与故障切换处理器模块

实现请求的重试和供应商切换逻辑。
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Optional

from app.config import get_settings
from app.providers.base import ProviderResponse
from app.rules.models import CandidateProvider
from app.services.strategy import SelectionStrategy


@dataclass
class RetryResult:
    """
    重试结果数据类
    
    封装重试执行后的结果信息。
    """
    
    # 最终响应
    response: ProviderResponse
    # 总重试次数
    retry_count: int
    # 最终使用的供应商
    final_provider: CandidateProvider
    # 是否成功
    success: bool


class RetryHandler:
    """
    重试与故障切换处理器
    
    实现以下重试逻辑：
    - 状态码 >= 500：对同一供应商重试，最多 3 次，每次间隔 1000ms
    - 状态码 < 500：直接切换到下一个供应商
    - 所有供应商都失败：返回最后一次失败的响应
    """
    
    def __init__(self, strategy: SelectionStrategy):
        """
        初始化处理器
        
        Args:
            strategy: 供应商选择策略
        """
        settings = get_settings()
        self.strategy = strategy
        # 同供应商最大重试次数
        self.max_retries = settings.RETRY_MAX_ATTEMPTS
        # 重试间隔（毫秒）
        self.retry_delay_ms = settings.RETRY_DELAY_MS
    
    async def execute_with_retry(
        self,
        candidates: list[CandidateProvider],
        requested_model: str,
        forward_fn: Callable[[CandidateProvider], Any],
    ) -> RetryResult:
        """
        带重试的请求执行
        
        Args:
            candidates: 候选供应商列表
            requested_model: 请求的模型名
            forward_fn: 转发函数，接受 CandidateProvider 返回 ProviderResponse
        
        Returns:
            RetryResult: 重试结果
        """
        if not candidates:
            return RetryResult(
                response=ProviderResponse(
                    status_code=503,
                    error="No available providers",
                ),
                retry_count=0,
                final_provider=None,  # type: ignore
                success=False,
            )
        
        # 记录已尝试的供应商
        tried_providers: set[int] = set()
        total_retry_count = 0
        last_response: Optional[ProviderResponse] = None
        last_provider: Optional[CandidateProvider] = None
        
        # 选择第一个供应商
        current_provider = await self.strategy.select(candidates, requested_model)
        
        while current_provider is not None:
            # 记录当前供应商已尝试
            tried_providers.add(current_provider.provider_id)
            last_provider = current_provider
            
            # 同供应商重试计数
            same_provider_retries = 0
            
            while same_provider_retries < self.max_retries:
                # 执行请求
                response = await forward_fn(current_provider)
                last_response = response
                
                # 成功响应
                if response.is_success:
                    return RetryResult(
                        response=response,
                        retry_count=total_retry_count,
                        final_provider=current_provider,
                        success=True,
                    )
                
                # 状态码 >= 500：同供应商重试
                if response.is_server_error:
                    same_provider_retries += 1
                    total_retry_count += 1
                    
                    if same_provider_retries < self.max_retries:
                        # 等待后重试
                        await asyncio.sleep(self.retry_delay_ms / 1000)
                        continue
                    else:
                        # 达到最大重试次数，切换供应商
                        break
                else:
                    # 状态码 < 500：直接切换供应商
                    total_retry_count += 1
                    break
            
            # 尝试切换到下一个供应商
            next_provider = await self._get_next_untried_provider(
                candidates, tried_providers
            )
            
            if next_provider is None:
                # 所有供应商都已尝试
                break
            
            current_provider = next_provider
        
        # 所有供应商都失败
        return RetryResult(
            response=last_response or ProviderResponse(
                status_code=503,
                error="All providers failed",
            ),
            retry_count=total_retry_count,
            final_provider=last_provider,  # type: ignore
            success=False,
        )
    
    async def _get_next_untried_provider(
        self,
        candidates: list[CandidateProvider],
        tried_providers: set[int],
    ) -> Optional[CandidateProvider]:
        """
        获取下一个未尝试的供应商
        
        Args:
            candidates: 候选供应商列表
            tried_providers: 已尝试的供应商 ID 集合
        
        Returns:
            Optional[CandidateProvider]: 下一个供应商
        """
        for candidate in candidates:
            if candidate.provider_id not in tried_providers:
                return candidate
        return None
