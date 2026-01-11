"""
日志 Repository 接口

定义请求日志数据访问的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.log import RequestLogModel, RequestLogCreate, RequestLogQuery


class LogRepository(ABC):
    """
    日志 Repository 抽象类
    
    定义请求日志数据访问的所有操作接口。
    """
    
    @abstractmethod
    async def create(self, data: RequestLogCreate) -> RequestLogModel:
        """
        创建请求日志
        
        Args:
            data: 创建数据
        
        Returns:
            RequestLogModel: 创建后的日志
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[RequestLogModel]:
        """
        根据 ID 获取日志
        
        Args:
            id: 日志 ID
        
        Returns:
            Optional[RequestLogModel]: 日志或 None
        """
        pass
    
    @abstractmethod
    async def query(self, query: RequestLogQuery) -> tuple[list[RequestLogModel], int]:
        """
        查询日志列表

        支持多条件过滤、分页和排序。

        Args:
            query: 查询条件

        Returns:
            tuple[list[RequestLogModel], int]: (日志列表, 总数)
        """
        pass

    @abstractmethod
    async def delete_older_than_days(self, days: int) -> int:
        """
        删除指定天数之前的日志

        Args:
            days: 保留天数，删除 days 天之前的日志

        Returns:
            int: 删除的日志数量
        """
        pass
