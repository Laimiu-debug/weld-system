"""
执行SQL脚本创建企业角色表
"""
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

def execute_sql_file(filename):
    """执行SQL文件"""
    try:
        # 读取SQL文件
        with open(filename, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 创建数据库引擎
        print("连接数据库...")
        # 使用简单的连接字符串
        engine = create_engine(
            "postgresql+psycopg2://postgres:123456@localhost:5432/sdweld1016",
            client_encoding='utf8'
        )

        # 执行SQL脚本
        print("执行SQL脚本...")
        with engine.connect() as conn:
            # 分割SQL语句（按分号分割，但保留DO块）
            statements = []
            current_stmt = []
            in_do_block = False

            for line in sql_script.split('\n'):
                line_stripped = line.strip()

                # 检测DO块的开始
                if line_stripped.startswith('DO $$') or line_stripped.startswith('DO$$'):
                    in_do_block = True
                    current_stmt.append(line)
                # 检测DO块的结束
                elif in_do_block and (line_stripped == '$$;' or line_stripped.startswith('END $$')):
                    current_stmt.append(line)
                    if line_stripped.endswith(';'):
                        statements.append('\n'.join(current_stmt))
                        current_stmt = []
                        in_do_block = False
                # 在DO块内
                elif in_do_block:
                    current_stmt.append(line)
                # 普通语句
                elif line_stripped and not line_stripped.startswith('--'):
                    current_stmt.append(line)
                    if line_stripped.endswith(';'):
                        statements.append('\n'.join(current_stmt))
                        current_stmt = []

            # 执行每个语句
            for i, stmt in enumerate(statements):
                if stmt.strip():
                    print(f"\n执行语句 {i+1}/{len(statements)}...")
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                        print(f"✅ 语句 {i+1} 执行成功")
                    except Exception as e:
                        print(f"❌ 语句 {i+1} 执行失败: {str(e)}")
                        # 继续执行下一个语句

        print("\n✅ SQL脚本执行完成！")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    execute_sql_file('backend/create_company_roles_table.sql')

