"""
API Key Repository SQLAlchemy 实现

提供 API Key 的具体数据库操作实现。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKey as ApiKeyORM
from app.domain.api_key import ApiKeyModel, ApiKeyCreate, ApiKeyUpdate
from app.repositories.api_key_repo import ApiKeyRepository


class SQLAlchemyApiKeyRepository(ApiKeyRepository):
    """
    API Key Repository SQLAlchemy 实现
    
    使用 SQLAlchemy ORM 实现 API Key 的数据库操作。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 异步数据库会话
        """
        self.session = session
    
    def _to_domain(self, entity: ApiKeyORM) -> ApiKeyModel:
        """将 ORM 实体转换为领域模型"""
        return ApiKeyModel(
            id=entity.id,
            key_name=entity.key_name,
            key_value=entity.key_value,
            is_active=entity.is_active,
            created_at=entity.created_at,
            last_used_at=entity.last_used_at,
        )
    
    async def create(self, data: ApiKeyCreate, key_value: str) -> ApiKeyModel:
        """创建 API Key"""
        entity = ApiKeyORM(
            key_name=data.key_name,
            key_value=key_value,
            is_active=True,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_domain(entity)
    
    async def get_by_id(self, id: int) -> Optional[ApiKeyModel]:
        """根据 ID 获取 API Key"""
        result = await self.session.execute(
            select(ApiKeyORM).where(ApiKeyORM.id == id)
        )
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None
    
    async def get_by_key_value(self, key_value: str) -> Optional[ApiKeyModel]:
        """根据 key 值获取 API Key（用于鉴权）"""
        result = await self.session.execute(
            select(ApiKeyORM).where(ApiKeyORM.key_value == key_value)
        )
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None
    
    async def get_by_name(self, key_name: str) -> Optional[ApiKeyModel]:
        """根据名称获取 API Key"""
        result = await self.session.execute(
            select(ApiKeyORM).where(ApiKeyORM.key_name == key_name)
        )
        entity = result.scalar_one_or_none()
        return self._to_domain(entity) if entity else None
    
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApiKeyModel], int]:
        """获取 API Key 列表"""
        query = select(ApiKeyORM)
        count_query = select(func.count()).select_from(ApiKeyORM)
        
        if is_active is not None:
            query = query.where(ApiKeyORM.is_active == is_active)
            count_query = count_query.where(ApiKeyORM.is_active == is_active)
        
        # 获取总数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页查询
        query = query.order_by(ApiKeyORM.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        entities = result.scalars().all()
        
        return [self._to_domain(e) for e in entities], total
    
    async def update(self, id: int, data: ApiKeyUpdate) -> Optional[ApiKeyModel]:
        """更新 API Key"""
        result = await self.session.execute(
            select(ApiKeyORM).where(ApiKeyORM.id == id)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)
        
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_domain(entity)
    
    async def update_last_used(self, id: int) -> None:
        """更新 API Key 的最后使用时间"""
        result = await self.session.execute(
            select(ApiKeyORM).where(ApiKeyORM.id == id)
        )
        entity = result.scalar_one_or_none()
        
        if entity:
            entity.last_used_at = datetime.utcnow()
            await self.session.commit()
    
    async def delete(self, id: int) -> bool:
        """删除 API Key"""
        result = await self.session.execute(
            select(ApiKeyORM).where(ApiKeyORM.id == id)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        await self.session.delete(entity)
        await self.session.commit()
        return True
