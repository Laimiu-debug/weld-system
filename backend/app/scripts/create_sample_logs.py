"""
创建模拟系统日志数据的脚本
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.models.system_log import SystemLog
from app.models.user import User

def create_sample_logs():
    """创建示例系统日志"""
    db = next(get_db())

    try:
        # 获取所有用户ID
        users = db.query(User).all()
        user_ids = [user.id for user in users]

        # 示例日志消息
        log_messages = [
            ("info", "api", "用户登录成功", None),
            ("info", "api", "用户获取数据", None),
            ("warning", "api", "API请求频率过高", None),
            ("error", "api", "数据库连接失败", "Connection timeout"),
            ("error", "auth", "用户认证失败", "Invalid token"),
            ("critical", "system", "磁盘空间不足", "Disk usage 95%"),
            ("error", "api", "文件上传失败", "File too large"),
            ("warning", "api", "权限不足", "Access denied"),
            ("info", "system", "系统备份完成", None),
            ("error", "database", "查询执行失败", "SQL syntax error"),
            ("critical", "api", "服务不可用", "Service unavailable"),
            ("warning", "auth", "密码过期", "Password expired"),
            ("info", "api", "数据导出完成", None),
            ("error", "api", "参数验证失败", "Invalid parameters"),
            ("warning", "system", "内存使用率过高", "Memory usage 85%"),
        ]

        # 创建日志条目
        logs_created = 0
        for i in range(100):  # 创建100条日志
            log_level, log_type, message, error_message = random.choice(log_messages)
            user_id = random.choice(user_ids + [None])  # 随机分配用户或无用户

            # 随机生成时间（最近7天内）
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            created_at = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            log = SystemLog(
                log_level=log_level,
                log_type=log_type,
                message=message,
                user_id=user_id,
                ip_address=f"192.168.1.{random.randint(1, 254)}",
                request_path=random.choice(["/api/v1/auth/login", "/api/v1/users", "/api/v1/admin/status", "/api/v1/files/upload"]),
                request_method=random.choice(["GET", "POST", "PUT", "DELETE"]),
                response_status=random.choice([200, 201, 400, 401, 403, 404, 500]),
                error_message=error_message,
                created_at=created_at
            )

            db.add(log)
            logs_created += 1

            if logs_created % 20 == 0:
                db.commit()

        db.commit()
        print(f"成功创建 {logs_created} 条系统日志")

    except Exception as e:
        print(f"创建日志失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_logs()