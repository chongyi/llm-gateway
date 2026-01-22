"""
Weighted Round Robin Strategy Unit Tests
"""

import pytest
import asyncio
from app.services.strategy import RoundRobinStrategy, PriorityStrategy
from app.rules.models import CandidateProvider


class TestWeightedRoundRobin:
    """Weighted Round Robin Tests"""
    
    def setup_method(self):
        """Setup before test"""
        self.strategy = RoundRobinStrategy()
        self.candidates = [
            CandidateProvider(
                provider_id=1,
                provider_name="ProviderA",
                base_url="",
                protocol="openai",
                api_key="",
                target_model="model",
                priority=0,
                weight=3,
            ),
            CandidateProvider(
                provider_id=2,
                provider_name="ProviderB",
                base_url="",
                protocol="openai",
                api_key="",
                target_model="model",
                priority=0,
                weight=1,
            ),
        ]

    @pytest.mark.asyncio
    async def test_weighted_selection(self):
        """Test weighted selection distribution"""
        self.strategy.reset()
        
        # Expected sequence for weights 3:1 is A, A, A, B
        
        # 1st selection -> A
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        # 2nd selection -> A
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        # 3rd selection -> A
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        # 4th selection -> B
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 2
        
        # 5th selection -> A (Loop back)
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1

    @pytest.mark.asyncio
    async def test_zero_or_negative_weight_fallback(self):
        """Test fallback to simple round robin when weights are invalid"""
        candidates = [
            CandidateProvider(
                provider_id=1,
                provider_name="ProviderA",
                base_url="",
                protocol="openai",
                api_key="",
                target_model="model",
                priority=0,
                weight=0, # Invalid
            ),
            CandidateProvider(
                provider_id=2,
                provider_name="ProviderB",
                base_url="",
                protocol="openai",
                api_key="",
                target_model="model",
                priority=0,
                weight=0, # Invalid
            ),
        ]
        
        self.strategy.reset()
        
        # Should behave as simple round robin (1:1)
        selected = await self.strategy.select(candidates, "test-model")
        assert selected.provider_id == 1
        
        selected = await self.strategy.select(candidates, "test-model")
        assert selected.provider_id == 2
        
        selected = await self.strategy.select(candidates, "test-model")
        assert selected.provider_id == 1


class TestWeightedPriorityStrategy:
    """Weighted Priority Strategy Tests"""
    
    def setup_method(self):
        """Setup before test"""
        self.strategy = PriorityStrategy()
        self.candidates = [
            CandidateProvider(
                provider_id=1,
                provider_name="ProviderA",
                base_url="",
                protocol="openai",
                api_key="",
                target_model="model",
                priority=0,
                weight=3,
            ),
            CandidateProvider(
                provider_id=2,
                provider_name="ProviderB",
                base_url="",
                protocol="openai",
                api_key="",
                target_model="model",
                priority=0,
                weight=1,
            ),
        ]

    @pytest.mark.asyncio
    async def test_weighted_priority_selection(self):
        """Test weighted selection within priority group"""
        self.strategy.reset()
        
        # Expected sequence for weights 3:1 is A, A, A, B
        
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
        
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 2
        
        selected = await self.strategy.select(self.candidates, "test-model")
        assert selected.provider_id == 1
