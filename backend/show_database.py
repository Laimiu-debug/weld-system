#!/usr/bin/env python3
"""
直接显示数据库数据的脚本
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.verification_code import VerificationCode
from sqlalchemy import text


def print_header(title):
    """打印标题"""
    print(f"\n{'='*80}")
    print(f" {title}")
    print(f"{'='*80}")


def show_all_users():
    """显示所有用户"""
    print_header("数据库中的所有用户")

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()

        print(f"总用户数: {len(users)}")
        print()

        print(f"{'ID':<5} {'邮箱':<30} {'用户名':<15} {'手机号':<15} {'公司':<15} {'状态':<8} {'会员等级':<12}")
        print("-" * 120)

        for user in users:
            status = "激活" if user.is_active else "禁用"
            member_tier = user.member_tier or "free"
            phone = user.phone or "未设置"
            username = user.username or "未设置"
            company = user.company or "未设置"

            # 截断过长的文本
            email = user.email[:28] + ".." if len(user.email) > 30 else user.email

            print(f"{user.id:<5} {email:<30} {username:<15} {phone:<15} {company:<15} {status:<8} {member_tier:<12}")

        # 显示统计信息
        active_users = [u for u in users if u.is_active]
        verified_users = [u for u in users if u.is_verified]
        super_users = [u for u in users if u.is_superuser]

        print(f"\n统计信息:")
        print(f"  - 总用户数: {len(users)}")
        print(f"  - 激活用户: {len(active_users)}")
        print(f"  - 已验证用户: {len(verified_users)}")
        print(f"  - 超级用户: {len(super_users)}")

        # 会员等级统计
        tier_stats = {}
        for user in users:
            tier = user.member_tier or "free"
            tier_stats[tier] = tier_stats.get(tier, 0) + 1

        print(f"\n会员等级分布:")
        for tier, count in tier_stats.items():
            print(f"  - {tier}: {count} 用户")

    finally:
        db.close()


def show_login_credentials():
    """显示登录凭据"""
    print_header("可用于登录的账号凭据")

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()

        print("可用于测试登录的账号:")
        print(f"{'账号类型':<10} {'账号':<25} {'密码':<20} {'备注':<15}")
        print("-" * 75)

        for user in users:
            # 优先显示手机号，如果没有则显示邮箱
            if user.phone:
                account = user.phone
                account_type = "手机号"
                password = "guohuAN123456" if user.phone == "13012410230" else "未知"
                note = "推荐测试账号" if user.phone == "13012410230" else "需要验证密码"
            else:
                account = user.email
                account_type = "邮箱"
                password = "未知"
                note = "需要验证密码"

            # 截断过长的账号
            account_display = account[:23] + ".." if len(account) > 25 else account

            print(f"{account_type:<10} {account_display:<25} {password:<20} {note:<15}")

        print(f"\n特别说明:")
        print(f"1. 手机号 13012410230 的确认密码是: guohuAN123456")
        print(f"2. 其他账号的密码可能需要重置或查看数据库哈希值")
        print(f"3. 推荐使用手机号 13012410230 进行测试登录")

    finally:
        db.close()


def show_recent_activity():
    """显示最近活动"""
    print_header("最近活动记录")

    db = SessionLocal()
    try:
        # 最近注册的用户
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()

        print("最近注册的用户 (前10个):")
        print(f"{'时间':<20} {'邮箱':<30} {'手机号':<15}")
        print("-" * 70)

        for user in recent_users:
            time_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            email = user.email[:28] + ".." if len(user.email) > 30 else user.email
            phone = user.phone or "未设置"
            print(f"{time_str:<20} {email:<30} {phone:<15}")

        # 最近的验证码
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)

        recent_codes = db.query(VerificationCode).filter(
            VerificationCode.created_at >= yesterday
        ).order_by(VerificationCode.created_at.desc()).limit(10).all()

        print(f"\n最近24小时的验证码记录 (前10个):")
        print(f"{'时间':<20} {'账号':<20} {'类型':<8} {'用途':<10} {'验证码':<8} {'状态':<8}")
        print("-" * 80)

        for code in recent_codes:
            time_str = code.created_at.strftime("%Y-%m-%d %H:%M:%S")
            account = code.account[:18] + ".." if len(code.account) > 20 else code.account
            used = "已使用" if code.is_used else "未使用"
            print(f"{time_str:<20} {account:<20} {code.account_type:<8} {code.purpose:<10} {code.code:<8} {used:<8}")

    finally:
        db.close()


def main():
    """主函数"""
    print("焊接系统数据库查看器")
    print("=" * 80)

    show_all_users()
    show_login_credentials()
    show_recent_activity()

    print_header("数据库查看完成")
    print("如需更多详细信息，可以使用 backend/database_viewer.py 交互式脚本")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()