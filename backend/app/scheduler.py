"""
定时任务调度模块

使用 APScheduler 管理定时任务，包括日志清理等。
"""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db.session import get_db
from app.repositories.sqlalchemy.log_repo import SQLAlchemyLogRepository
from app.services.log_service import LogService

logger = logging.getLogger(__name__)

# 全局调度器实例
_scheduler: Optional[AsyncIOScheduler] = None


async def cleanup_logs_task():
    """
    定时清理旧日志任务

    删除超过保留期限的日志记录。
    """
    settings = get_settings()
    logger.info(
        f"Starting scheduled log cleanup task (retention: {settings.LOG_RETENTION_DAYS} days)"
    )

    try:
        # 获取数据库会话
        async for db in get_db():
            # 创建服务实例
            log_repo = SQLAlchemyLogRepository(db)
            log_service = LogService(log_repo)

            # 执行清理
            deleted_count = await log_service.cleanup_old_logs(
                settings.LOG_RETENTION_DAYS
            )
            logger.info(f"Log cleanup task completed: {deleted_count} logs deleted")
            break  # 只需要一次迭代

    except Exception as e:
        logger.error(f"Log cleanup task failed: {str(e)}", exc_info=True)


def start_scheduler():
    """
    启动定时任务调度器

    初始化调度器并添加所有定时任务。
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already started")
        return

    settings = get_settings()

    # 创建调度器
    _scheduler = AsyncIOScheduler()

    # 添加日志清理任务（每天在配置的时间执行）
    _scheduler.add_job(
        cleanup_logs_task,
        trigger=CronTrigger(hour=settings.LOG_CLEANUP_HOUR, minute=0),
        id="cleanup_old_logs",
        name="清理旧日志",
        replace_existing=True,
    )

    # 启动调度器
    _scheduler.start()
    logger.info(
        f"Scheduler started: log cleanup scheduled daily at {settings.LOG_CLEANUP_HOUR}:00"
    )


def shutdown_scheduler():
    """
    关闭定时任务调度器

    优雅地停止所有定时任务。
    """
    global _scheduler

    if _scheduler is None:
        return

    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler shutdown completed")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """
    获取调度器实例

    Returns:
        Optional[AsyncIOScheduler]: 调度器实例或 None
    """
    return _scheduler
