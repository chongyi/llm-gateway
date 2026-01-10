"""
规则评估器模块

提供规则评估的核心逻辑。
"""

import re
from typing import Any, Optional

from app.rules.context import RuleContext
from app.rules.models import Rule, RuleSet


class RuleEvaluator:
    """
    规则评估器
    
    负责评估单条规则和规则集的匹配情况。
    
    支持的操作符：
    - eq: 等于
    - ne: 不等于
    - gt: 大于
    - gte: 大于等于
    - lt: 小于
    - lte: 小于等于
    - contains: 包含（字符串）
    - not_contains: 不包含（字符串）
    - regex: 正则匹配
    - in: 在列表中
    - not_in: 不在列表中
    - exists: 字段存在
    """
    
    def evaluate_rule(self, rule: Rule, context: RuleContext) -> bool:
        """
        评估单条规则
        
        Args:
            rule: 规则
            context: 规则上下文
        
        Returns:
            bool: 规则是否匹配
        """
        # 获取字段值
        actual_value = context.get_value(rule.field)
        expected_value = rule.value
        operator = rule.operator.lower()
        
        # 根据操作符评估
        try:
            if operator == "eq":
                return self._evaluate_eq(actual_value, expected_value)
            elif operator == "ne":
                return self._evaluate_ne(actual_value, expected_value)
            elif operator == "gt":
                return self._evaluate_gt(actual_value, expected_value)
            elif operator == "gte":
                return self._evaluate_gte(actual_value, expected_value)
            elif operator == "lt":
                return self._evaluate_lt(actual_value, expected_value)
            elif operator == "lte":
                return self._evaluate_lte(actual_value, expected_value)
            elif operator == "contains":
                return self._evaluate_contains(actual_value, expected_value)
            elif operator == "not_contains":
                return self._evaluate_not_contains(actual_value, expected_value)
            elif operator == "regex":
                return self._evaluate_regex(actual_value, expected_value)
            elif operator == "in":
                return self._evaluate_in(actual_value, expected_value)
            elif operator == "not_in":
                return self._evaluate_not_in(actual_value, expected_value)
            elif operator == "exists":
                return self._evaluate_exists(actual_value, expected_value)
            else:
                # 未知操作符，默认不匹配
                return False
        except Exception:
            # 评估出错，默认不匹配
            return False
    
    def evaluate_ruleset(
        self, ruleset: Optional[RuleSet], context: RuleContext
    ) -> bool:
        """
        评估规则集
        
        Args:
            ruleset: 规则集
            context: 规则上下文
        
        Returns:
            bool: 规则集是否匹配
        """
        # 空规则集默认通过
        if ruleset is None or ruleset.is_empty():
            return True
        
        results = [self.evaluate_rule(rule, context) for rule in ruleset.rules]
        
        if ruleset.logic == "OR":
            return any(results)
        else:  # AND（默认）
            return all(results)
    
    # ============ 操作符实现 ============
    
    def _evaluate_eq(self, actual: Any, expected: Any) -> bool:
        """等于"""
        return actual == expected
    
    def _evaluate_ne(self, actual: Any, expected: Any) -> bool:
        """不等于"""
        return actual != expected
    
    def _evaluate_gt(self, actual: Any, expected: Any) -> bool:
        """大于"""
        if actual is None:
            return False
        return actual > expected
    
    def _evaluate_gte(self, actual: Any, expected: Any) -> bool:
        """大于等于"""
        if actual is None:
            return False
        return actual >= expected
    
    def _evaluate_lt(self, actual: Any, expected: Any) -> bool:
        """小于"""
        if actual is None:
            return False
        return actual < expected
    
    def _evaluate_lte(self, actual: Any, expected: Any) -> bool:
        """小于等于"""
        if actual is None:
            return False
        return actual <= expected
    
    def _evaluate_contains(self, actual: Any, expected: Any) -> bool:
        """包含（字符串）"""
        if actual is None or not isinstance(actual, str):
            return False
        return str(expected) in actual
    
    def _evaluate_not_contains(self, actual: Any, expected: Any) -> bool:
        """不包含（字符串）"""
        if actual is None or not isinstance(actual, str):
            return True
        return str(expected) not in actual
    
    def _evaluate_regex(self, actual: Any, expected: Any) -> bool:
        """正则匹配"""
        if actual is None or not isinstance(actual, str):
            return False
        try:
            pattern = re.compile(str(expected))
            return bool(pattern.search(actual))
        except re.error:
            return False
    
    def _evaluate_in(self, actual: Any, expected: Any) -> bool:
        """在列表中"""
        if not isinstance(expected, (list, tuple)):
            return False
        return actual in expected
    
    def _evaluate_not_in(self, actual: Any, expected: Any) -> bool:
        """不在列表中"""
        if not isinstance(expected, (list, tuple)):
            return True
        return actual not in expected
    
    def _evaluate_exists(self, actual: Any, expected: Any) -> bool:
        """字段存在"""
        exists = actual is not None
        # expected 为 True 时检查存在，为 False 时检查不存在
        if expected:
            return exists
        return not exists
