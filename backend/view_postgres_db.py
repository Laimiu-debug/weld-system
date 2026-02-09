#!/usr/bin/env python3
"""
PostgreSQL数据库查看工具
用于查看焊接工艺管理系统的PostgreSQL数据库表结构和数据
"""

import psycopg2
import os
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'weld_user',
    'password': 'weld_password',
    'database': 'weld_db'
}

def connect_to_db():
    """连接到PostgreSQL数据库"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        return None

def show_database_info():
    """显示数据库基本信息"""
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # 数据库版本
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 PostgreSQL版本: {version[0]}")

        # 当前数据库
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()
        print(f"📊 当前数据库: {db_name[0]}")

        # 数据库大小
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()));
        """)
        size = cursor.fetchone()
        print(f"📊 数据库大小: {size[0]}")

    except Exception as e:
        print(f"❌ 获取数据库信息失败: {e}")
    finally:
        conn.close()

def show_all_tables():
    """显示所有表"""
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        print(f"\n📋 数据库表列表 (共{len(tables)}个表):")
        table_data = []
        for table in tables:
            table_data.append([table[0], f"{table[1]}列"])

        print(tabulate(table_data, headers=["表名", "字段数"], tablefmt="grid"))

    except Exception as e:
        print(f"❌ 获取表列表失败: {e}")
    finally:
        conn.close()

def show_table_structure(table_name):
    """显示表结构"""
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
        """, (table_name,))
        columns = cursor.fetchall()

        print(f"\n🏗️ 表 '{table_name}' 的结构:")
        column_data = []
        for col in columns:
            nullable = "✓" if col[2] == "YES" else "✗"
            default = col[3] if col[3] else ""
            column_data.append([col[0], col[1], nullable, default])

        print(tabulate(column_data, headers=["字段名", "类型", "可空", "默认值"], tablefmt="grid"))

    except Exception as e:
        print(f"❌ 获取表结构失败: {e}")
    finally:
        conn.close()

def show_table_data(table_name, limit=10):
    """显示表数据"""
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()['count']
        print(f"\n📊 表 '{table_name}' 数据 (共{count}条记录，显示前{limit}条):")

        # 获取数据
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
        records = cursor.fetchall()

        if records:
            # 转换为表格显示
            data = []
            for record in records:
                data.append([str(v) if v is not None else "NULL" for v in record.values()])

            headers = list(records[0].keys())
            print(tabulate(data, headers=headers, tablefmt="grid", maxcolwidths=20))
        else:
            print("表为空")

    except Exception as e:
        print(f"❌ 获取表数据失败: {e}")
    finally:
        conn.close()

def show_table_statistics():
    """显示表统计信息"""
    conn = connect_to_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT schemaname, tablename,
                   n_tup_ins as inserts,
                   n_tup_upd as updates,
                   n_tup_del as deletes,
                   n_live_tup as live_tuples,
                   n_dead_tup as dead_tuples
            FROM pg_stat_user_tables
            ORDER BY tablename;
        """)
        stats = cursor.fetchall()

        print(f"\n📈 表统计信息:")
        stat_data = []
        for stat in stats:
            stat_data.append([
                stat[1],  # tablename
                stat[2],  # inserts
                stat[3],  # updates
                stat[4],  # deletes
                stat[5],  # live_tuples
                stat[6]   # dead_tuples
            ])

        print(tabulate(stat_data,
                      headers=["表名", "插入", "更新", "删除", "活跃记录", "死记录"],
                      tablefmt="grid"))

    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
    finally:
        conn.close()

def main():
    """主菜单"""
    print("PostgreSQL数据库查看工具")
    print("=" * 50)

    while True:
        print("\n📋 选择操作:")
        print("1. 显示数据库基本信息")
        print("2. 显示所有表")
        print("3. 查看表结构")
        print("4. 查看表数据")
        print("5. 显示表统计信息")
        print("0. 退出")

        choice = input("\n请输入选项 (0-5): ").strip()

        if choice == "0":
            print("👋 再见!")
            break
        elif choice == "1":
            show_database_info()
        elif choice == "2":
            show_all_tables()
        elif choice == "3":
            table_name = input("请输入表名: ").strip()
            if table_name:
                show_table_structure(table_name)
        elif choice == "4":
            table_name = input("请输入表名: ").strip()
            if table_name:
                try:
                    limit = int(input("显示记录数 (默认10): ").strip() or "10")
                    show_table_data(table_name, limit)
                except ValueError:
                    print("❌ 请输入有效的数字")
        elif choice == "5":
            show_table_statistics()
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main()