"""
测试每日通知任务
"""
from app.core.database import SessionLocal
from app.services.notification_service import NotificationService

def test_daily_tasks():
    db = SessionLocal()
    try:
        service = NotificationService(db)
        
        print("🚀 开始运行每日通知任务...")
        
        # 测试到期提醒
        print("\n📅 检查即将到期的订阅...")
        count = service.send_expiration_reminders(days_ahead=7)
        print(f"✅ 发送了 {count} 条到期提醒")
        
        # 测试过期处理
        print("\n⏰ 处理已过期的订阅...")
        count = service.process_expired_subscriptions()
        print(f"✅ 处理了 {count} 个过期订阅")
        
        # 测试配额检查
        print("\n📊 检查配额使用情况...")
        count = service.check_and_notify_quota_usage()
        print(f"✅ 发送了 {count} 条配额警告")
        
        print("\n🎉 每日任务执行完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_daily_tasks()

