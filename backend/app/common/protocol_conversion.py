"""
协议转换（OpenAI <-> Anthropic）

在供应商协议与用户请求协议不一致时，将请求/响应在两种协议之间转换。
"""

from __future__ import annotations

import copy
import json
import time
import uuid
from typing import Any, AsyncGenerator, Optional

import httpx
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from app.common.errors import ServiceError
from app.common.stream_usage import SSEDecoder

try:
    from litellm.llms.anthropic.chat.transformation import AnthropicConfig
    from litellm.llms.anthropic.experimental_pass_through.transformation import (
        AnthropicExperimentalPassThroughConfig,
    )
    from litellm.types.utils import ModelResponse
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "litellm is required for protocol conversion. "
        "Install backend dependencies (see backend/requirements.txt)."
    ) from e


OPENAI_PROTOCOL = "openai"
ANTHROPIC_PROTOCOL = "anthropic"


def normalize_protocol(protocol: str) -> str:
    protocol = (protocol or OPENAI_PROTOCOL).lower().strip()
    if protocol not in (OPENAI_PROTOCOL, ANTHROPIC_PROTOCOL):
        raise ServiceError(message=f"Unsupported protocol '{protocol}'", code="unsupported_protocol")
    return protocol


def _encode_sse_data(payload: str) -> bytes:
    return f"data: {payload}\n\n".encode("utf-8")


def _encode_sse_json(obj: dict[str, Any]) -> bytes:
    return _encode_sse_data(json.dumps(obj, ensure_ascii=False))


def _map_anthropic_finish_reason_to_openai(stop_reason: Optional[str]) -> str:
    if not stop_reason:
        return "stop"
    if stop_reason == "end_turn":
        return "stop"
    if stop_reason == "max_tokens":
        return "length"
    if stop_reason == "tool_use":
        return "tool_calls"
    return "stop"


def convert_request_for_supplier(
    *,
    request_protocol: str,
    supplier_protocol: str,
    path: str,
    body: dict[str, Any],
    target_model: str,
) -> tuple[str, dict[str, Any]]:
    """
    将用户请求协议转换为供应商协议的请求体/路径。

    仅支持 Chat/Messages 的互转：
    - OpenAI: /v1/chat/completions
    - Anthropic: /v1/messages
    """
    request_protocol = normalize_protocol(request_protocol)
    supplier_protocol = normalize_protocol(supplier_protocol)

    if request_protocol == supplier_protocol:
        new_body = copy.deepcopy(body)
        new_body["model"] = target_model
        return path, new_body

    if request_protocol == OPENAI_PROTOCOL and supplier_protocol == ANTHROPIC_PROTOCOL:
        if path != "/v1/chat/completions":
            raise ServiceError(
                message=f"Unsupported OpenAI endpoint for conversion: {path}",
                code="unsupported_protocol_conversion",
            )
        openai_body = copy.deepcopy(body)
        messages = openai_body.get("messages")
        if not isinstance(messages, list):
            raise ServiceError(message="OpenAI request missing 'messages'", code="invalid_request")

        optional_params = {k: v for k, v in openai_body.items() if k not in ("model", "messages")}
        if "max_tokens" not in optional_params and "max_completion_tokens" in optional_params:
            optional_params["max_tokens"] = optional_params["max_completion_tokens"]
        if "max_tokens" not in optional_params:
            optional_params["max_tokens"] = 1024

        anthropic_body = AnthropicConfig().transform_request(
            model=target_model,
            messages=messages,
            optional_params=optional_params,
            litellm_params={},
            headers={},
        )
        return "/v1/messages", anthropic_body

    if request_protocol == ANTHROPIC_PROTOCOL and supplier_protocol == OPENAI_PROTOCOL:
        if path != "/v1/messages":
            raise ServiceError(
                message=f"Unsupported Anthropic endpoint for conversion: {path}",
                code="unsupported_protocol_conversion",
            )
        anthropic_body = copy.deepcopy(body)
        anthropic_body["model"] = target_model
        openai_body = AnthropicExperimentalPassThroughConfig().translate_anthropic_to_openai(
            anthropic_message_request=anthropic_body  # type: ignore[arg-type]
        )
        return "/v1/chat/completions", openai_body

    raise ServiceError(
        message=f"Unsupported protocol conversion: {request_protocol} -> {supplier_protocol}",
        code="unsupported_protocol_conversion",
    )


def convert_response_for_user(
    *,
    request_protocol: str,
    supplier_protocol: str,
    body: Any,
    target_model: str,
) -> Any:
    """
    将供应商响应转换为用户请求协议的响应体。
    """
    request_protocol = normalize_protocol(request_protocol)
    supplier_protocol = normalize_protocol(supplier_protocol)

    if request_protocol == supplier_protocol:
        return body

    if not isinstance(body, dict):
        return body

    if request_protocol == ANTHROPIC_PROTOCOL and supplier_protocol == OPENAI_PROTOCOL:
        model_response = ModelResponse(**body)
        translated = AnthropicExperimentalPassThroughConfig().translate_openai_response_to_anthropic(
            response=model_response
        )
        return translated.model_dump(exclude_none=True)

    if request_protocol == OPENAI_PROTOCOL and supplier_protocol == ANTHROPIC_PROTOCOL:
        dummy_logger = type("DummyLogger", (), {"post_call": lambda *args, **kwargs: None})()
        response = httpx.Response(200, json=body, headers={})
        model = body.get("model") or target_model
        model_response = AnthropicConfig().transform_response(
            model=model,
            raw_response=response,
            model_response=ModelResponse(),
            logging_obj=dummy_logger,
            request_data={},
            messages=[],
            optional_params={},
            litellm_params={},
            encoding=None,
            api_key="",
            json_mode=None,
        )
        return model_response.model_dump(exclude_none=True)

    raise ServiceError(
        message=f"Unsupported protocol conversion: {supplier_protocol} -> {request_protocol}",
        code="unsupported_protocol_conversion",
    )


async def convert_stream_for_user(
    *,
    request_protocol: str,
    supplier_protocol: str,
    upstream: AsyncGenerator[bytes, None],
    model: str,
) -> AsyncGenerator[bytes, None]:
    """
    将供应商 SSE bytes 流转换为用户请求协议的 SSE bytes 流。

    - OpenAI: data: {chat.completion.chunk}\n\n + data: [DONE]\n\n
    - Anthropic: data: {type: ...}\n\n
    """
    request_protocol = normalize_protocol(request_protocol)
    supplier_protocol = normalize_protocol(supplier_protocol)

    if request_protocol == supplier_protocol:
        async for chunk in upstream:
            yield chunk
        return

    if request_protocol == ANTHROPIC_PROTOCOL and supplier_protocol == OPENAI_PROTOCOL:
        decoder = SSEDecoder()
        cfg = AnthropicExperimentalPassThroughConfig()

        sent_message_start = False
        sent_content_block_start = False
        sent_content_block_finish = False
        sent_message_stop = False
        holding: Optional[dict[str, Any]] = None

        async for chunk in upstream:
            for payload in decoder.feed(chunk):
                if not payload:
                    continue
                if payload.strip() == "[DONE]":
                    continue

                if not sent_message_start:
                    sent_message_start = True
                    yield _encode_sse_json(
                        {
                            "type": "message_start",
                            "message": {
                                "id": f"msg_{uuid.uuid4().hex}",
                                "type": "message",
                                "role": "assistant",
                                "content": [],
                                "model": model,
                                "stop_reason": None,
                                "stop_sequence": None,
                                "usage": {"input_tokens": 0, "output_tokens": 0},
                            },
                        }
                    )
                if not sent_content_block_start:
                    sent_content_block_start = True
                    yield _encode_sse_json(
                        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}
                    )

                try:
                    data = json.loads(payload)
                except Exception:
                    continue

                try:
                    openai_chunk = ChatCompletionChunk(**data)
                except Exception:
                    continue

                processed = cfg.translate_streaming_openai_response_to_anthropic(response=openai_chunk)

                if processed.get("type") == "message_delta" and sent_content_block_finish is False:
                    holding = processed
                    sent_content_block_finish = True
                    yield _encode_sse_json({"type": "content_block_stop", "index": 0})
                    continue

                if holding is not None:
                    yield _encode_sse_json(holding)
                    holding = processed
                    continue

                yield _encode_sse_json(processed)

        if holding is not None:
            yield _encode_sse_json(holding)
            holding = None

        if sent_message_stop is False:
            sent_message_stop = True
            yield _encode_sse_json({"type": "message_stop"})
        return

    if request_protocol == OPENAI_PROTOCOL and supplier_protocol == ANTHROPIC_PROTOCOL:
        decoder = SSEDecoder()
        response_id: Optional[str] = None
        sent_role = False
        done = False

        async for chunk in upstream:
            for payload in decoder.feed(chunk):
                if not payload:
                    continue
                if payload.strip() == "[DONE]":
                    continue

                try:
                    data = json.loads(payload)
                except Exception:
                    continue

                event_type = data.get("type")
                if event_type == "message_start":
                    message = data.get("message", {})
                    if isinstance(message, dict):
                        response_id = message.get("id") or response_id
                    continue

                if event_type == "content_block_start":
                    content_block = data.get("content_block", {})
                    if isinstance(content_block, dict) and content_block.get("type") == "text":
                        text = content_block.get("text") or ""
                        if text:
                            delta: dict[str, Any] = {"content": text}
                            if not sent_role:
                                delta["role"] = "assistant"
                                sent_role = True
                            yield _encode_sse_json(
                                {
                                    "id": response_id or f"chatcmpl-{uuid.uuid4().hex}",
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": model,
                                    "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                                }
                            )
                    continue

                if event_type == "content_block_delta":
                    delta_obj = data.get("delta")
                    if isinstance(delta_obj, dict):
                        delta_type = delta_obj.get("type")
                        if delta_type == "text_delta":
                            text = delta_obj.get("text") or ""
                            if text:
                                delta: dict[str, Any] = {"content": text}
                                if not sent_role:
                                    delta["role"] = "assistant"
                                    sent_role = True
                                yield _encode_sse_json(
                                    {
                                        "id": response_id or f"chatcmpl-{uuid.uuid4().hex}",
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": model,
                                        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                                    }
                                )
                        elif delta_type == "input_json_delta":
                            partial_json = delta_obj.get("partial_json") or ""
                            if partial_json:
                                delta: dict[str, Any] = {
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": None,
                                            "type": "function",
                                            "function": {"name": None, "arguments": partial_json},
                                        }
                                    ]
                                }
                                if not sent_role:
                                    delta["role"] = "assistant"
                                    sent_role = True
                                yield _encode_sse_json(
                                    {
                                        "id": response_id or f"chatcmpl-{uuid.uuid4().hex}",
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": model,
                                        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                                    }
                                )
                    continue

                if event_type == "message_delta":
                    delta_dict = data.get("delta")
                    stop_reason = None
                    if isinstance(delta_dict, dict):
                        stop_reason = delta_dict.get("stop_reason")
                    finish_reason = _map_anthropic_finish_reason_to_openai(stop_reason)
                    yield _encode_sse_json(
                        {
                            "id": response_id or f"chatcmpl-{uuid.uuid4().hex}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
                        }
                    )
                    yield _encode_sse_data("[DONE]")
                    done = True
                    continue

                if event_type == "message_stop":
                    if not done:
                        yield _encode_sse_data("[DONE]")
                        done = True
                    continue

        if not done:
            yield _encode_sse_data("[DONE]")
        return

    raise ServiceError(
        message=f"Unsupported protocol conversion: {supplier_protocol} -> {request_protocol}",
        code="unsupported_protocol_conversion",
    )

