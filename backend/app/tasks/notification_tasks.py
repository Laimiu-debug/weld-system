"""
定时任务 - 自动通知任务
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def run_daily_notification_tasks():
    """
    每日通知任务
    建议在每天早上8点运行
    """
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        
        logger.info(f"[定时任务] 开始执行每日通知任务 - {datetime.utcnow()}")
        
        # 1. 检查并通知即将到期的会员（7天、3天、1天前）
        logger.info("[定时任务] 检查即将到期的会员...")
        expiring_count = notification_service.send_expiration_reminders(days_ahead=7)
        logger.info(f"[定时任务] 发送了 {expiring_count} 条会员到期提醒")
        
        # 2. 检查并通知已过期的会员
        logger.info("[定时任务] 检查已过期的会员...")
        expired_count = notification_service.process_expired_subscriptions()
        logger.info(f"[定时任务] 处理了 {expired_count} 个过期会员")
        
        # 3. 处理自动续费
        logger.info("[定时任务] 处理自动续费...")
        renewed_count = notification_service.process_auto_renewals()
        logger.info(f"[定时任务] 处理了 {renewed_count} 个自动续费")
        
        # 4. 检查配额使用情况
        logger.info("[定时任务] 检查配额使用情况...")
        quota_count = notification_service.check_and_notify_quota_usage()
        logger.info(f"[定时任务] 发送了 {quota_count} 条配额警告")

        logger.info("[定时任务] 检查焊工资质到期...")
        cert_count = notification_service.notify_expiring_welder_certs(days_ahead=30)
        logger.info(f"[定时任务] 发送了 {cert_count} 条焊工资质到期提醒")

        logger.info("[定时任务] 检查设备保修到期...")
        warranty_count = notification_service.notify_expiring_warranties(days_ahead=30)
        logger.info(f"[定时任务] 发送了 {warranty_count} 条设备保修到期提醒")

        logger.info(f"[定时任务] 每日通知任务完成 - {datetime.utcnow()}")

        return {
            "success": True,
            "expiring_count": expiring_count,
            "expired_count": expired_count,
            "renewed_count": renewed_count,
            "quota_count": quota_count,
            "cert_count": cert_count,
            "warranty_count": warranty_count,
        }
        
    except Exception as e:
        logger.error(f"[定时任务] 每日通知任务失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def run_hourly_notification_tasks():
    """
    每小时通知任务
    用于更频繁的检查
    """
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        
        logger.info(f"[定时任务] 开始执行每小时通知任务 - {datetime.utcnow()}")
        
        # 检查即将到期的会员（1天内）
        expiring_count = notification_service.send_expiration_reminders(days_ahead=1)
        logger.info(f"[定时任务] 发送了 {expiring_count} 条紧急到期提醒")
        
        logger.info(f"[定时任务] 每小时通知任务完成 - {datetime.utcnow()}")
        
        return {
            "success": True,
            "expiring_count": expiring_count,
        }
        
    except Exception as e:
        logger.error(f"[定时任务] 每小时通知任务失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


if __name__ == "__main__":
    # 可以直接运行此脚本进行测试
    print("运行每日通知任务...")
    result = run_daily_notification_tasks()
    print(f"结果: {result}")

