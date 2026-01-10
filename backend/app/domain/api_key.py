"""
API Key 领域模型

定义 API Key 相关的数据传输对象（DTO）。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiKeyBase(BaseModel):
    """API Key 基础模型"""
    
    # Key 名称
    key_name: str = Field(..., min_length=1, max_length=100, description="Key 名称")


class ApiKeyCreate(ApiKeyBase):
    """创建 API Key 请求模型"""
    pass
    # key_value 由后端自动生成，不需要客户端提供


class ApiKeyUpdate(BaseModel):
    """更新 API Key 请求模型"""
    
    key_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class ApiKeyModel(ApiKeyBase):
    """API Key 完整模型"""
    
    id: int = Field(..., description="API Key ID")
    key_value: str = Field(..., description="Key 值")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    class Config:
        from_attributes = True


class ApiKeyResponse(ApiKeyBase):
    """API Key 响应模型（key_value 脱敏）"""
    
    id: int = Field(..., description="API Key ID")
    # key_value 脱敏显示
    key_value: str = Field(..., description="Key 值（脱敏）")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyBase):
    """创建 API Key 响应模型（key_value 完整显示，仅此一次）"""
    
    id: int = Field(..., description="API Key ID")
    # 创建时完整返回 key_value，之后不再显示
    key_value: str = Field(..., description="Key 值（仅创建时完整显示）")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    class Config:
        from_attributes = True
