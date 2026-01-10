"""
规则引擎单元测试
"""

import pytest
from app.rules import RuleContext, TokenUsage, Rule, RuleSet, RuleEvaluator, RuleEngine
from app.domain.model import ModelMapping, ModelMappingProviderResponse
from app.domain.provider import Provider
from datetime import datetime


class TestRuleContext:
    """规则上下文测试"""
    
    def test_get_value_model(self):
        """测试获取 model 字段"""
        context = RuleContext(current_model="gpt-4")
        assert context.get_value("model") == "gpt-4"
    
    def test_get_value_headers(self):
        """测试获取 headers 字段"""
        context = RuleContext(
            current_model="gpt-4",
            headers={"x-priority": "high", "content-type": "application/json"},
        )
        assert context.get_value("headers.x-priority") == "high"
        assert context.get_value("headers.content-type") == "application/json"
    
    def test_get_value_body(self):
        """测试获取 body 字段"""
        context = RuleContext(
            current_model="gpt-4",
            request_body={
                "model": "gpt-4",
                "temperature": 0.7,
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
            },
        )
        assert context.get_value("body.model") == "gpt-4"
        assert context.get_value("body.temperature") == 0.7
    
    def test_get_value_body_nested(self):
        """测试获取嵌套的 body 字段"""
        context = RuleContext(
            current_model="gpt-4",
            request_body={
                "messages": [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"},
                ],
            },
        )
        assert context.get_value("body.messages[0].role") == "system"
        assert context.get_value("body.messages[1].content") == "Hello"
    
    def test_get_value_token_usage(self):
        """测试获取 token_usage 字段"""
        context = RuleContext(
            current_model="gpt-4",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        )
        assert context.get_value("token_usage.input_tokens") == 100
        assert context.get_value("token_usage.output_tokens") == 50
        assert context.get_value("token_usage.total_tokens") == 150
    
    def test_get_value_not_found(self):
        """测试获取不存在的字段"""
        context = RuleContext(current_model="gpt-4")
        assert context.get_value("headers.not-exist") is None
        assert context.get_value("body.not-exist") is None
        assert context.get_value("unknown.field") is None


class TestRuleEvaluator:
    """规则评估器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.evaluator = RuleEvaluator()
        self.context = RuleContext(
            current_model="gpt-4",
            headers={"x-priority": "high"},
            request_body={"temperature": 0.7, "max_tokens": 1000},
            token_usage=TokenUsage(input_tokens=500),
        )
    
    def test_eq_operator(self):
        """测试等于操作符"""
        rule = Rule(field="model", operator="eq", value="gpt-4")
        assert self.evaluator.evaluate_rule(rule, self.context) is True
        
        rule = Rule(field="model", operator="eq", value="gpt-3.5")
        assert self.evaluator.evaluate_rule(rule, self.context) is False
    
    def test_ne_operator(self):
        """测试不等于操作符"""
        rule = Rule(field="model", operator="ne", value="gpt-3.5")
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_gt_operator(self):
        """测试大于操作符"""
        rule = Rule(field="body.temperature", operator="gt", value=0.5)
        assert self.evaluator.evaluate_rule(rule, self.context) is True
        
        rule = Rule(field="body.temperature", operator="gt", value=0.7)
        assert self.evaluator.evaluate_rule(rule, self.context) is False
    
    def test_gte_operator(self):
        """测试大于等于操作符"""
        rule = Rule(field="body.temperature", operator="gte", value=0.7)
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_lt_operator(self):
        """测试小于操作符"""
        rule = Rule(field="token_usage.input_tokens", operator="lt", value=1000)
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_lte_operator(self):
        """测试小于等于操作符"""
        rule = Rule(field="token_usage.input_tokens", operator="lte", value=500)
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_contains_operator(self):
        """测试包含操作符"""
        rule = Rule(field="headers.x-priority", operator="contains", value="hi")
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_in_operator(self):
        """测试在列表中操作符"""
        rule = Rule(field="model", operator="in", value=["gpt-4", "gpt-3.5"])
        assert self.evaluator.evaluate_rule(rule, self.context) is True
        
        rule = Rule(field="model", operator="in", value=["claude-3"])
        assert self.evaluator.evaluate_rule(rule, self.context) is False
    
    def test_exists_operator(self):
        """测试存在操作符"""
        rule = Rule(field="headers.x-priority", operator="exists", value=True)
        assert self.evaluator.evaluate_rule(rule, self.context) is True
        
        rule = Rule(field="headers.not-exist", operator="exists", value=False)
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_regex_operator(self):
        """测试正则匹配操作符"""
        rule = Rule(field="model", operator="regex", value="gpt-\\d")
        assert self.evaluator.evaluate_rule(rule, self.context) is True
    
    def test_evaluate_ruleset_and(self):
        """测试规则集 AND 逻辑"""
        ruleset = RuleSet(
            rules=[
                Rule(field="model", operator="eq", value="gpt-4"),
                Rule(field="headers.x-priority", operator="eq", value="high"),
            ],
            logic="AND",
        )
        assert self.evaluator.evaluate_ruleset(ruleset, self.context) is True
        
        ruleset = RuleSet(
            rules=[
                Rule(field="model", operator="eq", value="gpt-4"),
                Rule(field="headers.x-priority", operator="eq", value="low"),
            ],
            logic="AND",
        )
        assert self.evaluator.evaluate_ruleset(ruleset, self.context) is False
    
    def test_evaluate_ruleset_or(self):
        """测试规则集 OR 逻辑"""
        ruleset = RuleSet(
            rules=[
                Rule(field="model", operator="eq", value="gpt-3.5"),
                Rule(field="headers.x-priority", operator="eq", value="high"),
            ],
            logic="OR",
        )
        assert self.evaluator.evaluate_ruleset(ruleset, self.context) is True
    
    def test_evaluate_empty_ruleset(self):
        """测试空规则集（默认通过）"""
        assert self.evaluator.evaluate_ruleset(None, self.context) is True
        assert self.evaluator.evaluate_ruleset(RuleSet(rules=[]), self.context) is True


class TestRuleEngine:
    """规则引擎测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = RuleEngine()
        now = datetime.utcnow()
        
        # 模拟供应商
        self.providers = {
            1: Provider(
                id=1,
                name="OpenAI",
                base_url="https://api.openai.com",
                protocol="openai",
                api_type="chat",
                api_key="sk-xxx",
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
            2: Provider(
                id=2,
                name="Azure",
                base_url="https://azure.openai.com",
                protocol="openai",
                api_type="chat",
                api_key="azure-xxx",
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
        }
        
        # 模拟模型映射
        self.model_mapping = ModelMapping(
            requested_model="gpt-4",
            strategy="round_robin",
            matching_rules=None,  # 无模型级规则
            capabilities=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        
        # 模拟模型-供应商映射
        self.provider_mappings = [
            ModelMappingProviderResponse(
                id=1,
                requested_model="gpt-4",
                provider_id=1,
                provider_name="OpenAI",
                target_model_name="gpt-4-0613",
                provider_rules=None,
                priority=1,
                weight=1,
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
            ModelMappingProviderResponse(
                id=2,
                requested_model="gpt-4",
                provider_id=2,
                provider_name="Azure",
                target_model_name="gpt-4-azure",
                provider_rules=None,
                priority=2,
                weight=1,
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
        ]
    
    def test_evaluate_no_rules(self):
        """测试无规则时所有供应商都匹配"""
        context = RuleContext(current_model="gpt-4")
        
        candidates = self.engine.evaluate_sync(
            context=context,
            model_mapping=self.model_mapping,
            provider_mappings=self.provider_mappings,
            providers=self.providers,
        )
        
        assert len(candidates) == 2
        assert candidates[0].provider_name == "OpenAI"
        assert candidates[0].target_model == "gpt-4-0613"
        assert candidates[1].provider_name == "Azure"
        assert candidates[1].target_model == "gpt-4-azure"
    
    def test_evaluate_with_model_rules(self):
        """测试模型级规则过滤"""
        context = RuleContext(
            current_model="gpt-4",
            headers={"x-priority": "low"},
        )
        
        # 设置模型级规则：只有 high 优先级才通过
        self.model_mapping.matching_rules = {
            "rules": [
                {"field": "headers.x-priority", "operator": "eq", "value": "high"}
            ]
        }
        
        candidates = self.engine.evaluate_sync(
            context=context,
            model_mapping=self.model_mapping,
            provider_mappings=self.provider_mappings,
            providers=self.providers,
        )
        
        # 模型级规则不通过，返回空列表
        assert len(candidates) == 0
    
    def test_evaluate_with_provider_rules(self):
        """测试供应商级规则过滤"""
        context = RuleContext(
            current_model="gpt-4",
            token_usage=TokenUsage(input_tokens=5000),
        )
        
        # 设置供应商级规则：OpenAI 只接受 input_tokens < 4000
        self.provider_mappings[0].provider_rules = {
            "rules": [
                {"field": "token_usage.input_tokens", "operator": "lt", "value": 4000}
            ]
        }
        
        candidates = self.engine.evaluate_sync(
            context=context,
            model_mapping=self.model_mapping,
            provider_mappings=self.provider_mappings,
            providers=self.providers,
        )
        
        # 只有 Azure 通过
        assert len(candidates) == 1
        assert candidates[0].provider_name == "Azure"
    
    def test_evaluate_inactive_provider(self):
        """测试未激活的供应商被过滤"""
        context = RuleContext(current_model="gpt-4")
        
        # 禁用 OpenAI
        self.providers[1].is_active = False
        
        candidates = self.engine.evaluate_sync(
            context=context,
            model_mapping=self.model_mapping,
            provider_mappings=self.provider_mappings,
            providers=self.providers,
        )
        
        assert len(candidates) == 1
        assert candidates[0].provider_name == "Azure"
    
    def test_evaluate_priority_sorting(self):
        """测试候选供应商按优先级排序"""
        context = RuleContext(current_model="gpt-4")
        
        # 调换优先级
        self.provider_mappings[0].priority = 10
        self.provider_mappings[1].priority = 1
        
        candidates = self.engine.evaluate_sync(
            context=context,
            model_mapping=self.model_mapping,
            provider_mappings=self.provider_mappings,
            providers=self.providers,
        )
        
        # Azure（优先级1）应该排在前面
        assert candidates[0].provider_name == "Azure"
        assert candidates[1].provider_name == "OpenAI"
