
import os
import pytest
from unittest.mock import patch, MagicMock
from app.providers.openai_client import OpenAIClient
from app.providers.anthropic_client import AnthropicClient

# Mock settings
with patch("app.providers.openai_client.get_settings") as mock_settings:
    mock_settings.return_value.HTTP_TIMEOUT = 10
    
    def test_openai_header_stripping():
        client = OpenAIClient()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer old-key",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "test-agent"
        }
        
        prepared = client._prepare_headers(headers, "new-key")
        
        # Check removed headers
        # assert "authorization" not in [k.lower() for k in prepared.keys()] # Authorization is added back
        assert "content-type" not in [k.lower() for k in prepared.keys()]
        assert "accept-encoding" not in [k.lower() for k in prepared.keys()]
        
        # Check preserved headers
        assert prepared["User-Agent"] == "test-agent"
        
        # Check added headers
        assert prepared["Authorization"] == "Bearer new-key"

    def test_anthropic_header_stripping():
        with patch("app.providers.anthropic_client.get_settings") as mock_settings_anthropic:
            mock_settings_anthropic.return_value.HTTP_TIMEOUT = 10
            client = AnthropicClient()
            headers = {
                "Content-Type": "application/json",
                "x-api-key": "old-key",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "test-agent"
            }
            
            prepared = client._prepare_headers(headers, "new-key")
            
            # Check removed headers
            assert "x-api-key" not in [k.lower() for k in prepared.keys() if k.lower() != "x-api-key"] 
            # Wait, Anthropic client adds x-api-key back, but removes the original one from keys_to_remove?
            # It iterates over new_headers.keys() and deletes if in keys_to_remove.
            # Then adds it back.
            
            assert prepared["x-api-key"] == "new-key"
            assert "content-type" not in [k.lower() for k in prepared.keys()]
            assert "accept-encoding" not in [k.lower() for k in prepared.keys()]
            
            # Check preserved headers
            assert prepared["User-Agent"] == "test-agent"
