"""
日志服务模块

提供请求日志的业务逻辑处理。
"""

from typing import Optional

from app.common.errors import NotFoundError
from app.domain.log import (
    RequestLogModel,
    RequestLogCreate,
    RequestLogResponse,
    RequestLogQuery,
)
from app.repositories.log_repo import LogRepository


class LogService:
    """
    日志服务
    
    处理请求日志相关的业务逻辑。
    """
    
    def __init__(self, repo: LogRepository):
        """
        初始化服务
        
        Args:
            repo: 日志 Repository
        """
        self.repo = repo
    
    async def create(self, data: RequestLogCreate) -> RequestLogModel:
        """
        创建请求日志
        
        Args:
            data: 创建数据
        
        Returns:
            RequestLogModel: 创建后的日志
        """
        return await self.repo.create(data)
    
    async def get_by_id(self, id: int) -> RequestLogModel:
        """
        根据 ID 获取日志详情
        
        Args:
            id: 日志 ID
        
        Returns:
            RequestLogModel: 日志详情
        
        Raises:
            NotFoundError: 日志不存在
        """
        log = await self.repo.get_by_id(id)
        if not log:
            raise NotFoundError(
                message=f"Request log with id {id} not found",
                code="log_not_found",
            )
        return log
    
    async def query(
        self, query: RequestLogQuery
    ) -> tuple[list[RequestLogResponse], int]:
        """
        查询日志列表
        
        Args:
            query: 查询条件
        
        Returns:
            tuple[list[RequestLogResponse], int]: (日志列表, 总数)
        """
        logs, total = await self.repo.query(query)
        
        # 转换为响应模型（列表展示不包含详细的请求/响应体）
        responses = [
            RequestLogResponse(
                id=log.id,
                request_time=log.request_time,
                api_key_id=log.api_key_id,
                api_key_name=log.api_key_name,
                requested_model=log.requested_model,
                target_model=log.target_model,
                provider_id=log.provider_id,
                provider_name=log.provider_name,
                retry_count=log.retry_count,
                first_byte_delay_ms=log.first_byte_delay_ms,
                total_time_ms=log.total_time_ms,
                input_tokens=log.input_tokens,
                output_tokens=log.output_tokens,
                response_status=log.response_status,
                trace_id=log.trace_id,
                is_stream=log.is_stream,
            )
            for log in logs
        ]
        
        return responses, total
