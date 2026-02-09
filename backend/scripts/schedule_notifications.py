#!/usr/bin/env python3
"""
定时任务脚本 - 处理会员到期提醒
"""
import sys
import os
import schedule
import time
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.notification_service import NotificationService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_expiring_subscriptions():
    """检查即将到期的订阅"""
    logger.info("开始检查即将到期的订阅...")
    
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        
        # 发送7天到期提醒
        sent_count = notification_service.send_expiration_reminders(days_ahead=7)
        logger.info(f"发送了 {sent_count} 条7天到期提醒")
        
        # 发送3天到期提醒
        sent_count = notification_service.send_expiration_reminders(days_ahead=3)
        logger.info(f"发送了 {sent_count} 条3天到期提醒")
        
        # 发送1天到期提醒
        sent_count = notification_service.send_expiration_reminders(days_ahead=1)
        logger.info(f"发送了 {sent_count} 条1天到期提醒")
        
    except Exception as e:
        logger.error(f"检查即将到期的订阅失败: {str(e)}")
    finally:
        db.close()


def process_expired_subscriptions():
    """
    处理已过期的订阅并自动切换会员等级

    使用新的会员等级计算服务，支持多订单场景下的自动切换
    """
    logger.info("开始处理已过期的订阅并自动切换会员等级...")

    db = SessionLocal()
    try:
        # 使用新的会员等级计算服务
        from app.services.membership_tier_service import MembershipTierService
        tier_service = MembershipTierService(db)

        # 检查并切换过期订阅
        results = tier_service.check_and_switch_expired_subscriptions()

        # 统计处理结果
        success_count = 0
        error_count = 0
        tier_changed_count = 0

        for result in results:
            if 'error' in result:
                error_count += 1
                logger.error(f"处理用户 {result['user_id']} 失败: {result['error']}")
            else:
                success_count += 1
                if result.get('changed'):
                    tier_changed_count += 1
                    logger.info(
                        f"用户 {result['user_id']} 会员等级已切换: "
                        f"{result['old_tier']} -> {result['new_tier']}"
                    )

        logger.info(
            f"处理完成: 成功 {success_count} 个, 失败 {error_count} 个, "
            f"等级变更 {tier_changed_count} 个"
        )

        # 同时使用通知服务发送通知（已更新为使用新服务）
        notification_service = NotificationService(db)
        notification_count = notification_service.process_expired_subscriptions()
        logger.info(f"发送了 {notification_count} 条通知")

    except Exception as e:
        logger.error(f"处理已过期的订阅失败: {str(e)}", exc_info=True)
    finally:
        db.close()


def process_auto_renewals():
    """处理自动续费"""
    logger.info("开始处理自动续费...")
    
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        
        # 处理自动续费
        renewed_count = notification_service.process_auto_renewals()
        logger.info(f"处理了 {renewed_count} 个自动续费")
        
    except Exception as e:
        logger.error(f"处理自动续费失败: {str(e)}")
    finally:
        db.close()


def daily_tasks():
    """每日任务"""
    logger.info("开始执行每日任务...")
    check_expiring_subscriptions()
    process_expired_subscriptions()
    process_auto_renewals()
    logger.info("每日任务执行完成")


def main():
    """主函数"""
    logger.info("启动定时任务调度器...")
    
    # 每天早上9点执行每日任务
    schedule.every().day.at("09:00").do(daily_tasks)
    
    # 每3小时检查一次即将到期的订阅
    schedule.every(3).hours.do(check_expiring_subscriptions)
    
    # 每天凌晨1点处理已过期的订阅
    schedule.every().day.at("01:00").do(process_expired_subscriptions)
    
    # 每天早上8点处理自动续费
    schedule.every().day.at("08:00").do(process_auto_renewals)
    
    logger.info("定时任务调度器已启动，按计划执行任务...")
    
    # 保持脚本运行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 如果传入参数，立即执行一次任务
    if len(sys.argv) > 1:
        if sys.argv[1] == "check-expiring":
            check_expiring_subscriptions()
        elif sys.argv[1] == "process-expired":
            process_expired_subscriptions()
        elif sys.argv[1] == "process-renewals":
            process_auto_renewals()
        elif sys.argv[1] == "daily":
            daily_tasks()
        else:
            print("未知参数。可用参数: check-expiring, process-expired, process-renewals, daily")
    else:
        # 启动定时任务调度器
        main()