"""
模型管理服务模块

提供模型映射和模型-供应商映射的业务逻辑处理。
"""

from typing import Optional

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.model import (
    ModelMapping,
    ModelMappingCreate,
    ModelMappingUpdate,
    ModelMappingResponse,
    ModelMappingProvider,
    ModelMappingProviderCreate,
    ModelMappingProviderUpdate,
    ModelMappingProviderResponse,
)
from app.repositories.model_repo import ModelRepository
from app.repositories.provider_repo import ProviderRepository


class ModelService:
    """
    模型管理服务
    
    处理模型映射和模型-供应商映射相关的业务逻辑。
    """
    
    def __init__(
        self,
        model_repo: ModelRepository,
        provider_repo: ProviderRepository,
    ):
        """
        初始化服务
        
        Args:
            model_repo: 模型 Repository
            provider_repo: 供应商 Repository
        """
        self.model_repo = model_repo
        self.provider_repo = provider_repo
    
    # ============ 模型映射操作 ============
    
    async def create_mapping(self, data: ModelMappingCreate) -> ModelMappingResponse:
        """
        创建模型映射
        
        Args:
            data: 创建数据
        
        Returns:
            ModelMappingResponse: 创建后的模型映射
        
        Raises:
            ConflictError: 模型已存在
        """
        # 检查模型是否已存在
        existing = await self.model_repo.get_mapping(data.requested_model)
        if existing:
            raise ConflictError(
                message=f"Model '{data.requested_model}' already exists",
                code="duplicate_model",
            )
        
        mapping = await self.model_repo.create_mapping(data)
        return await self._to_mapping_response(mapping)
    
    async def get_mapping(self, requested_model: str) -> ModelMappingResponse:
        """
        获取模型映射详情（含供应商配置）
        
        Args:
            requested_model: 请求模型名
        
        Returns:
            ModelMappingResponse: 模型映射详情
        
        Raises:
            NotFoundError: 模型不存在
        """
        mapping = await self.model_repo.get_mapping(requested_model)
        if not mapping:
            raise NotFoundError(
                message=f"Model '{requested_model}' not found",
                code="model_not_found",
            )
        
        return await self._to_mapping_response(mapping, include_providers=True)
    
    async def get_all_mappings(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ModelMappingResponse], int]:
        """
        获取模型映射列表
        
        Args:
            is_active: 过滤激活状态
            page: 页码
            page_size: 每页数量
        
        Returns:
            tuple[list[ModelMappingResponse], int]: (模型映射列表, 总数)
        """
        mappings, total = await self.model_repo.get_all_mappings(
            is_active, page, page_size
        )
        
        responses = []
        for mapping in mappings:
            responses.append(await self._to_mapping_response(mapping))
        
        return responses, total
    
    async def update_mapping(
        self, requested_model: str, data: ModelMappingUpdate
    ) -> ModelMappingResponse:
        """
        更新模型映射
        
        Args:
            requested_model: 请求模型名
            data: 更新数据
        
        Returns:
            ModelMappingResponse: 更新后的模型映射
        
        Raises:
            NotFoundError: 模型不存在
        """
        existing = await self.model_repo.get_mapping(requested_model)
        if not existing:
            raise NotFoundError(
                message=f"Model '{requested_model}' not found",
                code="model_not_found",
            )
        
        mapping = await self.model_repo.update_mapping(requested_model, data)
        return await self._to_mapping_response(mapping)  # type: ignore
    
    async def delete_mapping(self, requested_model: str) -> None:
        """
        删除模型映射
        
        Args:
            requested_model: 请求模型名
        
        Raises:
            NotFoundError: 模型不存在
        """
        existing = await self.model_repo.get_mapping(requested_model)
        if not existing:
            raise NotFoundError(
                message=f"Model '{requested_model}' not found",
                code="model_not_found",
            )
        
        await self.model_repo.delete_mapping(requested_model)
    
    # ============ 模型-供应商映射操作 ============
    
    async def create_provider_mapping(
        self, data: ModelMappingProviderCreate
    ) -> ModelMappingProviderResponse:
        """
        创建模型-供应商映射
        
        Args:
            data: 创建数据
        
        Returns:
            ModelMappingProviderResponse: 创建后的映射
        
        Raises:
            NotFoundError: 模型或供应商不存在
            ConflictError: 映射已存在
        """
        # 检查模型是否存在
        model = await self.model_repo.get_mapping(data.requested_model)
        if not model:
            raise NotFoundError(
                message=f"Model '{data.requested_model}' not found",
                code="model_not_found",
            )
        
        # 检查供应商是否存在
        provider = await self.provider_repo.get_by_id(data.provider_id)
        if not provider:
            raise NotFoundError(
                message=f"Provider with id {data.provider_id} not found",
                code="provider_not_found",
            )
        
        # 检查映射是否已存在
        existing = await self.model_repo.get_provider_mappings(
            requested_model=data.requested_model,
            provider_id=data.provider_id,
        )
        if existing:
            raise ConflictError(
                message=f"Mapping for model '{data.requested_model}' and provider {data.provider_id} already exists",
                code="duplicate_mapping",
            )
        
        return await self.model_repo.create_provider_mapping(data)
    
    async def get_provider_mappings(
        self,
        requested_model: Optional[str] = None,
        provider_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> list[ModelMappingProviderResponse]:
        """
        获取模型-供应商映射列表
        
        Args:
            requested_model: 按模型过滤
            provider_id: 按供应商过滤
            is_active: 过滤激活状态
        
        Returns:
            list[ModelMappingProviderResponse]: 映射列表
        """
        return await self.model_repo.get_provider_mappings(
            requested_model, provider_id, is_active
        )
    
    async def update_provider_mapping(
        self, id: int, data: ModelMappingProviderUpdate
    ) -> ModelMappingProviderResponse:
        """
        更新模型-供应商映射
        
        Args:
            id: 映射 ID
            data: 更新数据
        
        Returns:
            ModelMappingProviderResponse: 更新后的映射
        
        Raises:
            NotFoundError: 映射不存在
        """
        existing = await self.model_repo.get_provider_mapping(id)
        if not existing:
            raise NotFoundError(
                message=f"Model-provider mapping with id {id} not found",
                code="mapping_not_found",
            )
        
        result = await self.model_repo.update_provider_mapping(id, data)
        return result  # type: ignore
    
    async def delete_provider_mapping(self, id: int) -> None:
        """
        删除模型-供应商映射
        
        Args:
            id: 映射 ID
        
        Raises:
            NotFoundError: 映射不存在
        """
        existing = await self.model_repo.get_provider_mapping(id)
        if not existing:
            raise NotFoundError(
                message=f"Model-provider mapping with id {id} not found",
                code="mapping_not_found",
            )
        
        await self.model_repo.delete_provider_mapping(id)
    
    async def _to_mapping_response(
        self, mapping: ModelMapping, include_providers: bool = False
    ) -> ModelMappingResponse:
        """
        将 ModelMapping 转换为响应模型
        
        Args:
            mapping: 模型映射
            include_providers: 是否包含供应商列表
        
        Returns:
            ModelMappingResponse: 响应模型
        """
        provider_count = await self.model_repo.get_provider_count(
            mapping.requested_model
        )
        
        providers = None
        if include_providers:
            providers = await self.model_repo.get_provider_mappings(
                requested_model=mapping.requested_model
            )
        
        return ModelMappingResponse(
            requested_model=mapping.requested_model,
            strategy=mapping.strategy,
            matching_rules=mapping.matching_rules,
            capabilities=mapping.capabilities,
            is_active=mapping.is_active,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
            provider_count=provider_count,
            providers=providers,
        )
