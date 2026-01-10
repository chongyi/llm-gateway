"""
API Key Repository 接口

定义 API Key 数据访问的抽象接口。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.domain.api_key import ApiKeyModel, ApiKeyCreate, ApiKeyUpdate


class ApiKeyRepository(ABC):
    """
    API Key Repository 抽象类
    
    定义 API Key 数据访问的所有操作接口。
    """
    
    @abstractmethod
    async def create(self, data: ApiKeyCreate, key_value: str) -> ApiKeyModel:
        """
        创建 API Key
        
        Args:
            data: 创建数据
            key_value: 生成的 key 值
        
        Returns:
            ApiKeyModel: 创建后的 API Key
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[ApiKeyModel]:
        """
        根据 ID 获取 API Key
        
        Args:
            id: API Key ID
        
        Returns:
            Optional[ApiKeyModel]: API Key 或 None
        """
        pass
    
    @abstractmethod
    async def get_by_key_value(self, key_value: str) -> Optional[ApiKeyModel]:
        """
        根据 key 值获取 API Key（用于鉴权）
        
        Args:
            key_value: key 值
        
        Returns:
            Optional[ApiKeyModel]: API Key 或 None
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, key_name: str) -> Optional[ApiKeyModel]:
        """
        根据名称获取 API Key
        
        Args:
            key_name: key 名称
        
        Returns:
            Optional[ApiKeyModel]: API Key 或 None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApiKeyModel], int]:
        """
        获取 API Key 列表
        
        Args:
            is_active: 过滤激活状态
            page: 页码
            page_size: 每页数量
        
        Returns:
            tuple[list[ApiKeyModel], int]: (API Key 列表, 总数)
        """
        pass
    
    @abstractmethod
    async def update(self, id: int, data: ApiKeyUpdate) -> Optional[ApiKeyModel]:
        """
        更新 API Key
        
        Args:
            id: API Key ID
            data: 更新数据
        
        Returns:
            Optional[ApiKeyModel]: 更新后的 API Key 或 None
        """
        pass
    
    @abstractmethod
    async def update_last_used(self, id: int) -> None:
        """
        更新 API Key 的最后使用时间
        
        Args:
            id: API Key ID
        """
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """
        删除 API Key
        
        Args:
            id: API Key ID
        
        Returns:
            bool: 是否删除成功
        """
        pass
