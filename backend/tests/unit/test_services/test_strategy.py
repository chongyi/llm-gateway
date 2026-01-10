"""
轮询策略单元测试
"""

import pytest
import asyncio
from app.services.strategy import RoundRobinStrategy
from app.rules.models import CandidateProvider


class TestRoundRobinStrategy:
    """轮询策略测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.strategy = RoundRobinStrategy()
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
            CandidateProvider(
                provider_id=3,
                provider_name="Provider3",
                base_url="https://api3.com",
                protocol="openai",
                api_key="key3",
                target_model="model3",
                priority=3,
            ),
        ]
    
    @pytest.mark.asyncio
    async def test_select_round_robin(self):
        """测试轮询选择"""
        self.strategy.reset()
        
        # 第一次选择
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        # 第二次选择
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 2
        
        # 第三次选择
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 3
        
        # 第四次选择（回到第一个）
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
    
    @pytest.mark.asyncio
    async def test_select_empty_candidates(self):
        """测试空候选列表"""
        selected = await self.strategy.select([], "test-model")
        assert selected is None
    
    @pytest.mark.asyncio
    async def test_select_model_isolation(self):
        """测试不同模型的计数器隔离"""
        self.strategy.reset()
        
        # model-a 的选择
        selected_a = await self.strategy.select(self.candidates, "model-a")
        assert selected_a.provider_id == 1
        
        # model-b 的第一次选择（从头开始）
        selected_b = await self.strategy.select(self.candidates, "model-b")
        assert selected_b.provider_id == 1
        
        # model-a 的第二次选择
        selected_a = await self.strategy.select(self.candidates, "model-a")
        assert selected_a.provider_id == 2
    
    @pytest.mark.asyncio
    async def test_get_next(self):
        """测试获取下一个供应商"""
        current = self.candidates[0]
        next_provider = await self.strategy.get_next(
            self.candidates, "test-model", current
        )
        assert next_provider.provider_id == 2
        
        current = self.candidates[2]
        next_provider = await self.strategy.get_next(
            self.candidates, "test-model", current
        )
        assert next_provider.provider_id == 1
    
    @pytest.mark.asyncio
    async def test_get_next_single_candidate(self):
        """测试只有一个候选时获取下一个"""
        single = [self.candidates[0]]
        next_provider = await self.strategy.get_next(
            single, "test-model", single[0]
        )
        assert next_provider is None
    
    @pytest.mark.asyncio
    async def test_concurrent_selection(self):
        """测试并发选择的安全性"""
        self.strategy.reset()
        
        # 并发执行 100 次选择
        tasks = [
            self.strategy.select(self.candidates, "concurrent-test")
            for _ in range(100)
        ]
        results = await asyncio.gather(*tasks)
        
        # 验证结果分布（应该大致均匀）
        counts = {1: 0, 2: 0, 3: 0}
        for result in results:
            counts[result.provider_id] += 1
        
        # 每个供应商应该被选择约 33 次
        for provider_id, count in counts.items():
            assert 20 <= count <= 50, f"Provider {provider_id} selected {count} times"
