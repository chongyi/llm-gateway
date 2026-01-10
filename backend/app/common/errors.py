"""
错误定义模块

定义应用中使用的自定义异常类，统一错误处理。
"""

from typing import Any, Optional


class AppError(Exception):
    """
    应用基础异常类
    
    所有自定义异常的基类，包含错误消息、类型和代码。
    """
    
    def __init__(
        self,
        message: str,
        error_type: str = "app_error",
        code: str = "internal_error",
        details: Optional[dict[str, Any]] = None,
        status_code: int = 500,
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_type: 错误类型
            code: 错误代码
            details: 额外错误详情
            status_code: HTTP 状态码
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.code = code
        self.details = details or {}
        self.status_code = status_code
    
    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典格式（用于 API 响应）
        
        Returns:
            dict: 错误信息字典
        """
        result = {
            "error": {
                "message": self.message,
                "type": self.error_type,
                "code": self.code,
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result


class AuthenticationError(AppError):
    """
    认证错误
    
    当 API Key 无效或已禁用时抛出。
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "invalid_api_key",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="authentication_error",
            code=code,
            details=details,
            status_code=401,
        )


class NotFoundError(AppError):
    """
    资源不存在错误
    
    当请求的资源（如模型、供应商）不存在时抛出。
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "not_found",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="not_found_error",
            code=code,
            details=details,
            status_code=404,
        )


class ConflictError(AppError):
    """
    资源冲突错误
    
    当资源已存在（如重名）或被引用无法删除时抛出。
    """
    
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "conflict",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="conflict_error",
            code=code,
            details=details,
            status_code=409,
        )


class ValidationError(AppError):
    """
    参数校验错误
    
    当请求参数不符合要求时抛出。
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        code: str = "validation_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="validation_error",
            code=code,
            details=details,
            status_code=422,
        )


class UpstreamError(AppError):
    """
    上游服务错误
    
    当上游供应商返回错误或全部失败时抛出。
    """
    
    def __init__(
        self,
        message: str = "Upstream service error",
        code: str = "upstream_error",
        details: Optional[dict[str, Any]] = None,
        status_code: int = 502,
    ):
        super().__init__(
            message=message,
            error_type="upstream_error",
            code=code,
            details=details,
            status_code=status_code,
        )


class ServiceError(AppError):
    """
    服务错误
    
    当服务内部处理出错（如无可用供应商）时抛出。
    """
    
    def __init__(
        self,
        message: str = "Service error",
        code: str = "service_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="service_error",
            code=code,
            details=details,
            status_code=503,
        )
