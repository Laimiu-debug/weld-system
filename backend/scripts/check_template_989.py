"""
检查模板 989 的详细信息
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import engine

def check_template():
    """检查模板 989 的信息"""
    # 创建数据库连接
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 查询名称为 989 的模板
        result = db.execute(text("""
            SELECT
                id,
                name,
                module_type,
                workspace_type,
                template_source,
                module_instances,
                user_id,
                company_id,
                is_active
            FROM wps_templates
            WHERE name = '989'
            ORDER BY created_at DESC
            LIMIT 1
        """))
        
        row = result.fetchone()
        
        if row:
            print("=" * 60)
            print("模板 989 的详细信息:")
            print("=" * 60)
            print(f"ID: {row[0]}")
            print(f"名称: {row[1]}")
            print(f"模块类型 (module_type): {row[2]}")
            print(f"工作区类型 (workspace_type): {row[3]}")
            print(f"模板来源 (template_source): {row[4]}")
            print(f"模块实例数量: {len(row[5]) if row[5] else 0}")
            print(f"用户ID: {row[6]}")
            print(f"公司ID: {row[7]}")
            print(f"是否激活: {row[8]}")
            print("=" * 60)
            
            # 打印模块实例
            if row[5]:
                print("\n模块实例列表:")
                import json
                module_instances = row[5]
                for i, instance in enumerate(module_instances, 1):
                    print(f"\n  {i}. 实例ID: {instance.get('instanceId')}")
                    print(f"     模块ID: {instance.get('moduleId')}")
                    print(f"     顺序: {instance.get('order')}")
                    print(f"     自定义名称: {instance.get('customName', 'N/A')}")
            else:
                print("\n⚠️  警告: 该模板没有任何模块实例！")
            
            # 检查 module_type
            if row[2] != 'pqr':
                print(f"\n⚠️  警告: module_type 应该是 'pqr'，但实际是 '{row[2]}'")
                print("需要更新 module_type 为 'pqr'")

                # 询问是否更新
                response = input("\n是否将 module_type 更新为 'pqr'? (y/n): ")
                if response.lower() == 'y':
                    db.execute(text(f"""
                        UPDATE wps_templates
                        SET module_type = 'pqr'
                        WHERE id = '{row[0]}'
                    """))
                    db.commit()
                    print("✅ module_type 已更新为 'pqr'")
        else:
            print("❌ 未找到 ID 为 989 的模板")
            
            # 列出所有模板
            print("\n所有模板列表:")
            result = db.execute(text("""
                SELECT id, name, module_type, workspace_type 
                FROM wps_templates 
                ORDER BY id DESC 
                LIMIT 10
            """))
            
            for row in result:
                print(f"  ID: {row[0]}, 名称: {row[1]}, 类型: {row[2]}, 工作区: {row[3]}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_template()

