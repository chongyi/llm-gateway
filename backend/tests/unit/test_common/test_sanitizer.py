"""
脱敏模块单元测试
"""

import pytest
from app.common.sanitizer import (
    sanitize_authorization,
    sanitize_headers,
    sanitize_api_key_display,
)


class TestSanitizeAuthorization:
    """authorization 脱敏测试"""
    
    def test_bearer_token(self):
        """测试 Bearer token 脱敏"""
        result = sanitize_authorization("Bearer sk-1234567890abcdef")
        assert result.startswith("Bearer sk-1")
        assert "***" in result
        assert result.endswith("ef")
    
    def test_plain_token(self):
        """测试普通 token 脱敏"""
        result = sanitize_authorization("lgw-abcdefghijklmnop")
        assert result.startswith("lgw-")
        assert "***" in result
    
    def test_short_token(self):
        """测试短 token 脱敏"""
        result = sanitize_authorization("short")
        assert result == "***"
    
    def test_empty_value(self):
        """测试空值"""
        assert sanitize_authorization("") == ""
        assert sanitize_authorization(None) is None


class TestSanitizeHeaders:
    """请求头脱敏测试"""
    
    def test_sanitize_authorization_header(self):
        """测试 authorization 头脱敏"""
        headers = {
            "authorization": "Bearer sk-1234567890abcdef",
            "content-type": "application/json",
        }
        result = sanitize_headers(headers)
        
        assert "***" in result["authorization"]
        assert result["content-type"] == "application/json"
    
    def test_sanitize_x_api_key_header(self):
        """测试 x-api-key 头脱敏"""
        headers = {
            "x-api-key": "sk-1234567890abcdef",
            "user-agent": "test",
        }
        result = sanitize_headers(headers)
        
        assert "***" in result["x-api-key"]
        assert result["user-agent"] == "test"
    
    def test_not_modify_original(self):
        """测试不修改原始数据"""
        headers = {
            "authorization": "Bearer sk-1234567890abcdef",
        }
        original = headers["authorization"]
        
        result = sanitize_headers(headers)
        
        assert headers["authorization"] == original
        assert result is not headers
    
    def test_empty_headers(self):
        """测试空请求头"""
        assert sanitize_headers({}) == {}
        assert sanitize_headers(None) == {}


class TestSanitizeApiKeyDisplay:
    """API Key 显示脱敏测试"""
    
    def test_sanitize_api_key(self):
        """测试 API Key 脱敏"""
        result = sanitize_api_key_display("lgw-abcdefghijklmnopqrstuvwxyz")
        assert result.startswith("lgw-")
        assert "***" in result
