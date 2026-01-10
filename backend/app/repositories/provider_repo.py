"""
供应商 Repository 接口

定义供应商数据访问的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.provider import Provider, ProviderCreate, ProviderUpdate


class ProviderRepository(ABC):
    """
    供应商 Repository 抽象类
    
    定义供应商数据访问的所有操作接口。
    """
    
    @abstractmethod
    async def create(self, data: ProviderCreate) -> Provider:
        """
        创建供应商
        
        Args:
            data: 创建数据
        
        Returns:
            Provider: 创建后的供应商
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Provider]:
        """
        根据 ID 获取供应商
        
        Args:
            id: 供应商 ID
        
        Returns:
            Optional[Provider]: 供应商或 None
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Provider]:
        """
        根据名称获取供应商
        
        Args:
            name: 供应商名称
        
        Returns:
            Optional[Provider]: 供应商或 None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Provider], int]:
        """
        获取供应商列表
        
        Args:
            is_active: 过滤激活状态
            page: 页码
            page_size: 每页数量
        
        Returns:
            tuple[list[Provider], int]: (供应商列表, 总数)
        """
        pass
    
    @abstractmethod
    async def update(self, id: int, data: ProviderUpdate) -> Optional[Provider]:
        """
        更新供应商
        
        Args:
            id: 供应商 ID
            data: 更新数据
        
        Returns:
            Optional[Provider]: 更新后的供应商或 None
        """
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """
        删除供应商
        
        Args:
            id: 供应商 ID
        
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def has_model_mappings(self, id: int) -> bool:
        """
        检查供应商是否有关联的模型映射
        
        Args:
            id: 供应商 ID
        
        Returns:
            bool: 是否有关联
        """
        pass
