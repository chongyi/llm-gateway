"""
重试处理器单元测试
"""

import pytest
from unittest.mock import AsyncMock
from app.services.retry_handler import RetryHandler
from app.services.strategy import RoundRobinStrategy
from app.providers.base import ProviderResponse
from app.rules.models import CandidateProvider


class TestRetryHandler:
    """重试处理器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.strategy = RoundRobinStrategy()
        self.handler = RetryHandler(self.strategy)
        self.handler.max_retries = 3
        self.handler.retry_delay_ms = 10  # 加快测试
        
        self.candidates = [
            CandidateProvider(
                provider_id=1,
                provider_name="Provider1",
                base_url="https://api1.com",
                protocol="openai",
                api_key="key1",
                target_model="model1",
                priority=1,
            ),
            CandidateProvider(
                provider_id=2,
                provider_name="Provider2",
                base_url="https://api2.com",
                protocol="openai",
                api_key="key2",
                target_model="model2",
                priority=2,
            ),
        ]
    
    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """测试第一次就成功"""
        self.strategy.reset()
        
        async def forward_fn(candidate):
            return ProviderResponse(status_code=200, body={"result": "ok"})
        
        result = await self.handler.execute_with_retry(
            candidates=self.candidates,
            requested_model="test",
            forward_fn=forward_fn,
        )
        
        assert result.success is True
        assert result.retry_count == 0
        assert result.response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_retry_on_500_error(self):
        """测试 500 错误时重试"""
        self.strategy.reset()
        call_count = 0
        
        async def forward_fn(candidate):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return ProviderResponse(status_code=500, error="Server error")
            return ProviderResponse(status_code=200, body={"result": "ok"})
        
        result = await self.handler.execute_with_retry(
            candidates=self.candidates,
            requested_model="test",
            forward_fn=forward_fn,
        )
        
        assert result.success is True
        assert result.retry_count == 2  # 重试了 2 次后成功
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_switch_provider_on_400_error(self):
        """测试 400 错误时切换供应商"""
        self.strategy.reset()
        provider_calls = []
        
        async def forward_fn(candidate):
            provider_calls.append(candidate.provider_id)
            if candidate.provider_id == 1:
                return ProviderResponse(status_code=400, error="Bad request")
            return ProviderResponse(status_code=200, body={"result": "ok"})
        
        result = await self.handler.execute_with_retry(
            candidates=self.candidates,
            requested_model="test",
            forward_fn=forward_fn,
        )
        
        assert result.success is True
        assert result.final_provider.provider_id == 2
        # 第一个供应商失败后直接切换到第二个
        assert provider_calls == [1, 2]
    
    @pytest.mark.asyncio
    async def test_max_retries_then_switch(self):
        """测试达到最大重试次数后切换供应商"""
        self.strategy.reset()
        provider_calls = []
        
        async def forward_fn(candidate):
            provider_calls.append(candidate.provider_id)
            if candidate.provider_id == 1:
                return ProviderResponse(status_code=500, error="Server error")
            return ProviderResponse(status_code=200, body={"result": "ok"})
        
        result = await self.handler.execute_with_retry(
            candidates=self.candidates,
            requested_model="test",
            forward_fn=forward_fn,
        )
        
        assert result.success is True
        assert result.final_provider.provider_id == 2
        # Provider1 重试 3 次后切换到 Provider2
        assert provider_calls == [1, 1, 1, 2]
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """测试所有供应商都失败"""
        self.strategy.reset()
        
        async def forward_fn(candidate):
            return ProviderResponse(status_code=500, error="Server error")
        
        result = await self.handler.execute_with_retry(
            candidates=self.candidates,
            requested_model="test",
            forward_fn=forward_fn,
        )
        
        assert result.success is False
        assert result.response.status_code == 500
        # 每个供应商重试 3 次，共 6 次
        assert result.retry_count == 6
    
    @pytest.mark.asyncio
    async def test_empty_candidates(self):
        """测试空候选列表"""
        result = await self.handler.execute_with_retry(
            candidates=[],
            requested_model="test",
            forward_fn=AsyncMock(),
        )
        
        assert result.success is False
        assert result.response.status_code == 503
