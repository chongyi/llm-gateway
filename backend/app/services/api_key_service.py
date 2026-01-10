"""
API Key 管理服务模块

提供 API Key 的业务逻辑处理。
"""

from typing import Optional

from app.common.errors import ConflictError, NotFoundError, AuthenticationError
from app.common.sanitizer import sanitize_api_key_display
from app.common.utils import generate_api_key
from app.domain.api_key import (
    ApiKeyModel,
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyCreateResponse,
)
from app.repositories.api_key_repo import ApiKeyRepository


class ApiKeyService:
    """
    API Key 管理服务
    
    处理 API Key 相关的业务逻辑，包括创建、鉴权等。
    """
    
    def __init__(self, repo: ApiKeyRepository):
        """
        初始化服务
        
        Args:
            repo: API Key Repository
        """
        self.repo = repo
    
    async def create(self, data: ApiKeyCreate) -> ApiKeyCreateResponse:
        """
        创建 API Key
        
        key_value 由系统自动生成。
        
        Args:
            data: 创建数据
        
        Returns:
            ApiKeyCreateResponse: 创建后的 API Key（key_value 完整显示）
        
        Raises:
            ConflictError: 名称已存在
        """
        # 检查名称是否已存在
        existing = await self.repo.get_by_name(data.key_name)
        if existing:
            raise ConflictError(
                message=f"API Key with name '{data.key_name}' already exists",
                code="duplicate_name",
            )
        
        # 生成随机 key_value
        key_value = generate_api_key()
        
        api_key = await self.repo.create(data, key_value)
        
        # 创建时返回完整的 key_value
        return ApiKeyCreateResponse(
            id=api_key.id,
            key_name=api_key.key_name,
            key_value=api_key.key_value,  # 完整显示
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
        )
    
    async def get_by_id(self, id: int) -> ApiKeyResponse:
        """
        根据 ID 获取 API Key
        
        Args:
            id: API Key ID
        
        Returns:
            ApiKeyResponse: API Key 信息（key_value 脱敏）
        
        Raises:
            NotFoundError: API Key 不存在
        """
        api_key = await self.repo.get_by_id(id)
        if not api_key:
            raise NotFoundError(
                message=f"API Key with id {id} not found",
                code="api_key_not_found",
            )
        return self._to_response(api_key)
    
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApiKeyResponse], int]:
        """
        获取 API Key 列表
        
        Args:
            is_active: 过滤激活状态
            page: 页码
            page_size: 每页数量
        
        Returns:
            tuple[list[ApiKeyResponse], int]: (API Key 列表, 总数)
        """
        api_keys, total = await self.repo.get_all(is_active, page, page_size)
        return [self._to_response(k) for k in api_keys], total
    
    async def update(self, id: int, data: ApiKeyUpdate) -> ApiKeyResponse:
        """
        更新 API Key
        
        Args:
            id: API Key ID
            data: 更新数据
        
        Returns:
            ApiKeyResponse: 更新后的 API Key
        
        Raises:
            NotFoundError: API Key 不存在
            ConflictError: 名称已被其他 Key 使用
        """
        existing = await self.repo.get_by_id(id)
        if not existing:
            raise NotFoundError(
                message=f"API Key with id {id} not found",
                code="api_key_not_found",
            )
        
        # 如果更新名称，检查是否与其他 Key 冲突
        if data.key_name and data.key_name != existing.key_name:
            name_conflict = await self.repo.get_by_name(data.key_name)
            if name_conflict:
                raise ConflictError(
                    message=f"API Key with name '{data.key_name}' already exists",
                    code="duplicate_name",
                )
        
        api_key = await self.repo.update(id, data)
        return self._to_response(api_key)  # type: ignore
    
    async def delete(self, id: int) -> None:
        """
        删除 API Key
        
        Args:
            id: API Key ID
        
        Raises:
            NotFoundError: API Key 不存在
        """
        existing = await self.repo.get_by_id(id)
        if not existing:
            raise NotFoundError(
                message=f"API Key with id {id} not found",
                code="api_key_not_found",
            )
        
        await self.repo.delete(id)
    
    async def authenticate(self, key_value: str) -> ApiKeyModel:
        """
        验证 API Key
        
        Args:
            key_value: API Key 值
        
        Returns:
            ApiKeyModel: 验证通过的 API Key
        
        Raises:
            AuthenticationError: 验证失败
        """
        if not key_value:
            raise AuthenticationError(
                message="API Key is required",
                code="invalid_api_key",
            )
        
        # 去除 Bearer 前缀
        if key_value.lower().startswith("bearer "):
            key_value = key_value[7:]
        
        api_key = await self.repo.get_by_key_value(key_value)
        
        if not api_key:
            raise AuthenticationError(
                message="Invalid API Key",
                code="invalid_api_key",
            )
        
        if not api_key.is_active:
            raise AuthenticationError(
                message="API Key is disabled",
                code="api_key_disabled",
            )
        
        # 更新最后使用时间
        await self.repo.update_last_used(api_key.id)
        
        return api_key
    
    def _to_response(self, api_key: ApiKeyModel) -> ApiKeyResponse:
        """
        将 ApiKeyModel 转换为响应模型（key_value 脱敏）
        
        Args:
            api_key: API Key 模型
        
        Returns:
            ApiKeyResponse: 响应模型
        """
        return ApiKeyResponse(
            id=api_key.id,
            key_name=api_key.key_name,
            key_value=sanitize_api_key_display(api_key.key_value),
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
        )
