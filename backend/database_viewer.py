#!/usr/bin/env python3
"""
数据库查看器脚本 - 用于查看焊接系统数据库中的数据
"""
import sys
import os
from datetime import datetime
from typing import Optional

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.verification_code import VerificationCode
from sqlalchemy import text


def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_user_table(users):
    """打印用户表格"""
    if not users:
        print("没有找到用户数据")
        return

    print(f"{'ID':<5} {'邮箱':<30} {'用户名':<15} {'手机号':<15} {'公司':<15} {'状态':<8} {'会员等级':<12}")
    print("-" * 110)

    for user in users:
        status = "激活" if user.is_active else "禁用"
        member_tier = user.member_tier or "free"
        phone = user.phone or "未设置"
        username = user.username or "未设置"
        company = user.company or "未设置"

        print(f"{user.id:<5} {user.email:<30} {username:<15} {phone:<15} {company:<15} {status:<8} {member_tier:<12}")


def print_verification_codes(codes):
    """打印验证码表格"""
    if not codes:
        print("没有找到验证码数据")
        return

    print(f"{'ID':<5} {'账号':<25} {'类型':<8} {'用途':<10} {'验证码':<8} {'已使用':<8} {'过期时间':<20}")
    print("-" * 100)

    for code in codes:
        used = "是" if code.is_used else "否"
        expires = code.expires_at.strftime("%Y-%m-%d %H:%M:%S") if code.expires_at else "未设置"
        account = code.account[:22] + "..." if len(code.account) > 25 else code.account

        print(f"{code.id:<5} {account:<25} {code.account_type:<8} {code.purpose:<10} {code.code:<8} {used:<8} {expires:<20}")


def view_all_users():
    """查看所有用户"""
    print_header("所有用户数据")

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        print(f"总用户数: {len(users)}")
        print()
        print_user_table(users)

        # 显示一些统计信息
        active_users = [u for u in users if u.is_active]
        verified_users = [u for u in users if u.is_verified]

        print(f"\n统计信息:")
        print(f"  - 总用户数: {len(users)}")
        print(f"  - 激活用户: {len(active_users)}")
        print(f"  - 已验证用户: {len(verified_users)}")

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


def search_user(search_term: str):
    """搜索用户"""
    print_header(f"搜索用户: {search_term}")

    db = SessionLocal()
    try:
        # 支持按邮箱、用户名、手机号搜索
        users = db.query(User).filter(
            (User.email.ilike(f"%{search_term}%")) |
            (User.username.ilike(f"%{search_term}%")) |
            (User.phone.ilike(f"%{search_term}%")) |
            (User.company.ilike(f"%{search_term}%"))
        ).all()

        if not users:
            print(f"没有找到包含 '{search_term}' 的用户")
            return

        print(f"找到 {len(users)} 个匹配的用户:")
        print()
        print_user_table(users)

    finally:
        db.close()


def view_user_details(user_id: int):
    """查看用户详细信息"""
    print_header(f"用户详细信息 (ID: {user_id})")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"用户ID {user_id} 不存在")
            return

        print(f"基本信息:")
        print(f"  ID: {user.id}")
        print(f"  邮箱: {user.email}")
        print(f"  用户名: {user.username or '未设置'}")
        print(f"  联系方式: {user.contact or '未设置'}")
        print(f"  手机号: {user.phone or '未设置'}")
        print(f"  公司: {user.company or '未设置'}")
        print(f"  全名: {user.full_name or '未设置'}")
        print(f"  状态: {'激活' if user.is_active else '禁用'}")
        print(f"  邮箱验证: {'已验证' if user.is_verified else '未验证'}")
        print(f"  超级用户: {'是' if user.is_superuser else '否'}")
        print(f"  会员等级: {user.member_tier or 'free'}")
        print(f"  创建时间: {user.created_at}")
        print(f"  更新时间: {user.updated_at}")

    finally:
        db.close()


def view_verification_codes():
    """查看验证码"""
    print_header("验证码数据")

    db = SessionLocal()
    try:
        # 查看最近24小时的验证码
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)

        codes = db.query(VerificationCode).filter(
            VerificationCode.created_at >= yesterday
        ).order_by(VerificationCode.created_at.desc()).all()

        print(f"最近24小时验证码记录: {len(codes)}")
        print()
        print_verification_codes(codes)

    finally:
        db.close()


def view_database_stats():
    """查看数据库统计信息"""
    print_header("数据库统计信息")

    db = SessionLocal()
    try:
        # 使用原生SQL查询统计信息
        result = db.execute(text("""
            SELECT
                'users' as table_name,
                COUNT(*) as total_count,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                COUNT(CASE WHEN is_verified = true THEN 1 END) as verified_count
            FROM users
            UNION ALL
            SELECT
                'verification_codes' as table_name,
                COUNT(*) as total_count,
                COUNT(CASE WHEN is_used = false AND expires_at > NOW() THEN 1 END) as active_count,
                0 as verified_count
            FROM verification_codes
        """))

        print("表统计:")
        print(f"{'表名':<20} {'总记录数':<10} {'有效记录':<10} {'其他':<10}")
        print("-" * 55)

        for row in result:
            table_name = row.table_name
            total = row.total_count
            active = row.active_count if table_name == 'users' else row.active_count
            other = row.verified_count if table_name == 'users' else (total - active)

            print(f"{table_name:<20} {total:<10} {active:<10} {other:<10}")

        # 查看最近的用户注册
        print(f"\n最近注册的用户:")
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
        for user in recent_users:
            print(f"  - {user.email} ({user.created_at.strftime('%Y-%m-%d %H:%M')})")

    finally:
        db.close()


def main_menu():
    """主菜单"""
    while True:
        print_header("焊接系统数据库查看器")
        print("请选择操作:")
        print("1. 查看所有用户")
        print("2. 搜索用户")
        print("3. 查看用户详细信息")
        print("4. 查看验证码记录")
        print("5. 查看数据库统计")
        print("6. 测试登录凭据")
        print("0. 退出")

        choice = input("\n请输入选项 (0-6): ").strip()

        if choice == "1":
            view_all_users()
        elif choice == "2":
            search_term = input("请输入搜索关键词 (邮箱/用户名/手机号): ").strip()
            if search_term:
                search_user(search_term)
        elif choice == "3":
            try:
                user_id = int(input("请输入用户ID: ").strip())
                view_user_details(user_id)
            except ValueError:
                print("无效的用户ID")
        elif choice == "4":
            view_verification_codes()
        elif choice == "5":
            view_database_stats()
        elif choice == "6":
            test_login_credentials()
        elif choice == "0":
            print("再见!")
            break
        else:
            print("无效选项，请重新选择")

        input("\n按回车键继续...")


def test_login_credentials():
    """测试登录凭据"""
    print_header("测试登录凭据")

    print("数据库中的用户账号:")
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()

        print("\n可用于测试的账号:")
        print(f"{'邮箱/手机号':<25} {'密码提示':<15} {'用户类型':<10}")
        print("-" * 55)

        for user in users:
            # 如果有手机号，显示手机号；否则显示邮箱
            identifier = user.phone if user.phone else user.email
            password_hint = "guohuAN123456" if user.phone == "13012410230" else "未知"
            user_type = "管理员" if user.is_superuser else "普通用户"

            print(f"{identifier:<25} {password_hint:<15} {user_type:<10}")

        print(f"\n特别注意:")
        print(f"- 手机号 13012410230 的密码是: guohuAN123456")
        print(f"- 其他用户的密码需要自行设置或查看数据库")

    finally:
        db.close()


if __name__ == "__main__":
    print("焊接系统数据库查看器启动...")
    print("确保数据库服务正在运行...")

    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()