"""
测试日志清理功能
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.domain.log import RequestLogCreate
from app.repositories.sqlalchemy.log_repo import SQLAlchemyLogRepository
from app.services.log_service import LogService


@pytest.mark.asyncio
async def test_delete_older_than_days(db_session):
    """测试删除指定天数之前的日志"""
    repo = SQLAlchemyLogRepository(db_session)

    # 创建测试数据：3 条旧日志（10 天前）和 2 条新日志（3 天前）
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    recent_time = datetime.now(timezone.utc) - timedelta(days=3)

    # 创建旧日志
    for i in range(3):
        await repo.create(
            RequestLogCreate(
                request_time=old_time,
                api_key_id=1,
                api_key_name="test-key",
                requested_model="gpt-4",
                target_model="gpt-4",
                provider_id=1,
                provider_name="OpenAI",
                retry_count=0,
                matched_provider_count=1,
                first_byte_delay_ms=100,
                total_time_ms=500,
                input_tokens=10,
                output_tokens=20,
                response_status=200,
                trace_id=f"old-trace-{i}",
                is_stream=False,
            )
        )

    # 创建新日志
    for i in range(2):
        await repo.create(
            RequestLogCreate(
                request_time=recent_time,
                api_key_id=1,
                api_key_name="test-key",
                requested_model="gpt-4",
                target_model="gpt-4",
                provider_id=1,
                provider_name="OpenAI",
                retry_count=0,
                matched_provider_count=1,
                first_byte_delay_ms=100,
                total_time_ms=500,
                input_tokens=10,
                output_tokens=20,
                response_status=200,
                trace_id=f"recent-trace-{i}",
                is_stream=False,
            )
        )

    # 删除 7 天之前的日志
    deleted_count = await repo.delete_older_than_days(7)

    # 验证删除了 3 条旧日志
    assert deleted_count == 3


@pytest.mark.asyncio
async def test_delete_older_than_days_no_matching_logs(db_session):
    """测试当没有符合条件的日志时"""
    repo = SQLAlchemyLogRepository(db_session)

    # 创建一条最近的日志
    recent_time = datetime.now(timezone.utc) - timedelta(days=2)
    await repo.create(
        RequestLogCreate(
            request_time=recent_time,
            api_key_id=1,
            api_key_name="test-key",
            requested_model="gpt-4",
            target_model="gpt-4",
            provider_id=1,
            provider_name="OpenAI",
            retry_count=0,
            matched_provider_count=1,
            first_byte_delay_ms=100,
            total_time_ms=500,
            input_tokens=10,
            output_tokens=20,
            response_status=200,
            trace_id="trace-1",
            is_stream=False,
        )
    )

    # 删除 7 天之前的日志（应该没有符合条件的）
    deleted_count = await repo.delete_older_than_days(7)

    # 验证没有删除任何日志
    assert deleted_count == 0


@pytest.mark.asyncio
async def test_cleanup_old_logs_service(db_session):
    """测试服务层的日志清理方法"""
    repo = SQLAlchemyLogRepository(db_session)
    service = LogService(repo)

    # 创建旧日志
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    await repo.create(
        RequestLogCreate(
            request_time=old_time,
            api_key_id=1,
            api_key_name="test-key",
            requested_model="gpt-4",
            target_model="gpt-4",
            provider_id=1,
            provider_name="OpenAI",
            retry_count=0,
            matched_provider_count=1,
            first_byte_delay_ms=100,
            total_time_ms=500,
            input_tokens=10,
            output_tokens=20,
            response_status=200,
            trace_id="old-trace",
            is_stream=False,
        )
    )

    # 创建新日志
    recent_time = datetime.now(timezone.utc) - timedelta(days=3)
    await repo.create(
        RequestLogCreate(
            request_time=recent_time,
            api_key_id=1,
            api_key_name="test-key",
            requested_model="gpt-4",
            target_model="gpt-4",
            provider_id=1,
            provider_name="OpenAI",
            retry_count=0,
            matched_provider_count=1,
            first_byte_delay_ms=100,
            total_time_ms=500,
            input_tokens=10,
            output_tokens=20,
            response_status=200,
            trace_id="recent-trace",
            is_stream=False,
        )
    )

    # 清理 7 天之前的日志
    deleted_count = await service.cleanup_old_logs(7)

    # 验证只删除了旧日志
    assert deleted_count == 1
