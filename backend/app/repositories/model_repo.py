"""
模型 Repository 接口

定义模型映射和模型-供应商映射数据访问的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.model import (
    ModelMapping,
    ModelMappingCreate,
    ModelMappingUpdate,
    ModelMappingProvider,
    ModelMappingProviderCreate,
    ModelMappingProviderUpdate,
)


class ModelRepository(ABC):
    """
    模型 Repository 抽象类
    
    定义模型映射和模型-供应商映射数据访问的所有操作接口。
    """
    
    # ============ 模型映射操作 ============
    
    @abstractmethod
    async def create_mapping(self, data: ModelMappingCreate) -> ModelMapping:
        """
        创建模型映射
        
        Args:
            data: 创建数据
        
        Returns:
            ModelMapping: 创建后的模型映射
        """
        pass
    
    @abstractmethod
    async def get_mapping(self, requested_model: str) -> Optional[ModelMapping]:
        """
        根据请求模型名获取模型映射
        
        Args:
            requested_model: 请求模型名
        
        Returns:
            Optional[ModelMapping]: 模型映射或 None
        """
        pass
    
    @abstractmethod
    async def get_all_mappings(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ModelMapping], int]:
        """
        获取模型映射列表
        
        Args:
            is_active: 过滤激活状态
            page: 页码
            page_size: 每页数量
        
        Returns:
            tuple[list[ModelMapping], int]: (模型映射列表, 总数)
        """
        pass
    
    @abstractmethod
    async def update_mapping(
        self, requested_model: str, data: ModelMappingUpdate
    ) -> Optional[ModelMapping]:
        """
        更新模型映射
        
        Args:
            requested_model: 请求模型名
            data: 更新数据
        
        Returns:
            Optional[ModelMapping]: 更新后的模型映射或 None
        """
        pass
    
    @abstractmethod
    async def delete_mapping(self, requested_model: str) -> bool:
        """
        删除模型映射（同时删除关联的供应商映射）
        
        Args:
            requested_model: 请求模型名
        
        Returns:
            bool: 是否删除成功
        """
        pass
    
    # ============ 模型-供应商映射操作 ============
    
    @abstractmethod
    async def create_provider_mapping(
        self, data: ModelMappingProviderCreate
    ) -> ModelMappingProvider:
        """
        创建模型-供应商映射
        
        Args:
            data: 创建数据
        
        Returns:
            ModelMappingProvider: 创建后的映射
        """
        pass
    
    @abstractmethod
    async def get_provider_mapping(self, id: int) -> Optional[ModelMappingProvider]:
        """
        根据 ID 获取模型-供应商映射
        
        Args:
            id: 映射 ID
        
        Returns:
            Optional[ModelMappingProvider]: 映射或 None
        """
        pass
    
    @abstractmethod
    async def get_provider_mappings(
        self,
        requested_model: Optional[str] = None,
        provider_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> list[ModelMappingProvider]:
        """
        获取模型-供应商映射列表
        
        Args:
            requested_model: 按请求模型过滤
            provider_id: 按供应商过滤
            is_active: 过滤激活状态
        
        Returns:
            list[ModelMappingProvider]: 映射列表
        """
        pass
    
    @abstractmethod
    async def update_provider_mapping(
        self, id: int, data: ModelMappingProviderUpdate
    ) -> Optional[ModelMappingProvider]:
        """
        更新模型-供应商映射
        
        Args:
            id: 映射 ID
            data: 更新数据
        
        Returns:
            Optional[ModelMappingProvider]: 更新后的映射或 None
        """
        pass
    
    @abstractmethod
    async def delete_provider_mapping(self, id: int) -> bool:
        """
        删除模型-供应商映射
        
        Args:
            id: 映射 ID
        
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_provider_count(self, requested_model: str) -> int:
        """
        获取模型关联的供应商数量
        
        Args:
            requested_model: 请求模型名
        
        Returns:
            int: 供应商数量
        """
        pass
