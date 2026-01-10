"""
数据库会话管理模块

提供异步数据库会话管理，支持 SQLite 和 PostgreSQL。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

# 获取配置
settings = get_settings()

# 创建异步数据库引擎
# echo=True 在 DEBUG 模式下打印 SQL 语句
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # SQLite 特定配置
    connect_args={"check_same_thread": False} 
    if settings.DATABASE_TYPE == "sqlite" 
    else {},
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不自动过期对象，避免额外查询
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（依赖注入用）
    
    使用 async with 确保会话正确关闭。
    在 FastAPI 中作为 Depends 使用。
    
    Yields:
        AsyncSession: 异步数据库会话
    
    Example:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库
    
    创建所有定义的表结构。在应用启动时调用。
    
    Note:
        生产环境建议使用 Alembic 进行数据库迁移管理。
    """
    from app.db.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
