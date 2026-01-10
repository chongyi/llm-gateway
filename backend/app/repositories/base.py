"""
Repository 基类

定义数据访问层的通用抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

# 泛型类型变量
T = TypeVar("T")  # 实体类型
CreateT = TypeVar("CreateT", bound=BaseModel)  # 创建模型类型
UpdateT = TypeVar("UpdateT", bound=BaseModel)  # 更新模型类型


class BaseRepository(ABC, Generic[T, CreateT, UpdateT]):
    """
    Repository 抽象基类
    
    定义通用的 CRUD 操作接口，具体实现由子类提供。
    
    Type Parameters:
        T: 实体类型
        CreateT: 创建模型类型
        UpdateT: 更新模型类型
    """
    
    @abstractmethod
    async def create(self, data: CreateT) -> T:
        """
        创建实体
        
        Args:
            data: 创建数据
        
        Returns:
            T: 创建后的实体
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
        """
        根据 ID 获取实体
        
        Args:
            id: 实体 ID
        
        Returns:
            Optional[T]: 实体或 None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        **filters: Any
    ) -> tuple[list[T], int]:
        """
        获取实体列表
        
        Args:
            page: 页码
            page_size: 每页数量
            **filters: 过滤条件
        
        Returns:
            tuple[list[T], int]: (实体列表, 总数)
        """
        pass
    
    @abstractmethod
    async def update(self, id: Any, data: UpdateT) -> Optional[T]:
        """
        更新实体
        
        Args:
            id: 实体 ID
            data: 更新数据
        
        Returns:
            Optional[T]: 更新后的实体或 None
        """
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """
        删除实体
        
        Args:
            id: 实体 ID
        
        Returns:
            bool: 是否删除成功
        """
        pass
