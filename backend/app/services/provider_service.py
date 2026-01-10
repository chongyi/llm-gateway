"""
供应商管理服务模块

提供供应商的业务逻辑处理。
"""

from typing import Optional

from app.common.errors import ConflictError, NotFoundError
from app.common.sanitizer import sanitize_api_key_display
from app.domain.provider import Provider, ProviderCreate, ProviderUpdate, ProviderResponse
from app.repositories.provider_repo import ProviderRepository


class ProviderService:
    """
    供应商管理服务
    
    处理供应商相关的业务逻辑，包括 CRUD 操作和业务规则验证。
    """
    
    def __init__(self, repo: ProviderRepository):
        """
        初始化服务
        
        Args:
            repo: 供应商 Repository
        """
        self.repo = repo
    
    async def create(self, data: ProviderCreate) -> ProviderResponse:
        """
        创建供应商
        
        Args:
            data: 创建数据
        
        Returns:
            ProviderResponse: 创建后的供应商（API Key 脱敏）
        
        Raises:
            ConflictError: 名称已存在
        """
        # 检查名称是否已存在
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise ConflictError(
                message=f"Provider with name '{data.name}' already exists",
                code="duplicate_name",
            )
        
        provider = await self.repo.create(data)
        return self._to_response(provider)
    
    async def get_by_id(self, id: int) -> ProviderResponse:
        """
        根据 ID 获取供应商
        
        Args:
            id: 供应商 ID
        
        Returns:
            ProviderResponse: 供应商信息（API Key 脱敏）
        
        Raises:
            NotFoundError: 供应商不存在
        """
        provider = await self.repo.get_by_id(id)
        if not provider:
            raise NotFoundError(
                message=f"Provider with id {id} not found",
                code="provider_not_found",
            )
        return self._to_response(provider)
    
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ProviderResponse], int]:
        """
        获取供应商列表
        
        Args:
            is_active: 过滤激活状态
            page: 页码
            page_size: 每页数量
        
        Returns:
            tuple[list[ProviderResponse], int]: (供应商列表, 总数)
        """
        providers, total = await self.repo.get_all(is_active, page, page_size)
        return [self._to_response(p) for p in providers], total
    
    async def update(self, id: int, data: ProviderUpdate) -> ProviderResponse:
        """
        更新供应商
        
        Args:
            id: 供应商 ID
            data: 更新数据
        
        Returns:
            ProviderResponse: 更新后的供应商
        
        Raises:
            NotFoundError: 供应商不存在
            ConflictError: 名称已被其他供应商使用
        """
        # 检查供应商是否存在
        existing = await self.repo.get_by_id(id)
        if not existing:
            raise NotFoundError(
                message=f"Provider with id {id} not found",
                code="provider_not_found",
            )
        
        # 如果更新名称，检查是否与其他供应商冲突
        if data.name and data.name != existing.name:
            name_conflict = await self.repo.get_by_name(data.name)
            if name_conflict:
                raise ConflictError(
                    message=f"Provider with name '{data.name}' already exists",
                    code="duplicate_name",
                )
        
        provider = await self.repo.update(id, data)
        return self._to_response(provider)  # type: ignore
    
    async def delete(self, id: int) -> None:
        """
        删除供应商
        
        Args:
            id: 供应商 ID
        
        Raises:
            NotFoundError: 供应商不存在
            ConflictError: 供应商被模型映射引用
        """
        # 检查供应商是否存在
        existing = await self.repo.get_by_id(id)
        if not existing:
            raise NotFoundError(
                message=f"Provider with id {id} not found",
                code="provider_not_found",
            )
        
        # 检查是否被引用
        if await self.repo.has_model_mappings(id):
            raise ConflictError(
                message="Provider is referenced by model mappings",
                code="provider_in_use",
            )
        
        await self.repo.delete(id)
    
    def _to_response(self, provider: Provider) -> ProviderResponse:
        """
        将 Provider 转换为响应模型（API Key 脱敏）
        
        Args:
            provider: 供应商模型
        
        Returns:
            ProviderResponse: 响应模型
        """
        return ProviderResponse(
            id=provider.id,
            name=provider.name,
            base_url=provider.base_url,
            protocol=provider.protocol,
            api_type=provider.api_type,
            api_key=sanitize_api_key_display(provider.api_key) if provider.api_key else None,
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )
