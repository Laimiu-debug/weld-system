"""
检查WPS模板数据
"""
from app.core.database import engine
from sqlalchemy import text

def check_templates():
    """检查系统模板"""
    with engine.connect() as conn:
        # 查询系统模板
        result = conn.execute(text(
            "SELECT id, name, welding_process, welding_process_name, is_system "
            "FROM wps_templates "
            "WHERE is_system = TRUE "
            "ORDER BY welding_process"
        ))
        
        print("\n" + "=" * 100)
        print("系统WPS模板列表")
        print("=" * 100)
        print(f"{'模板ID':<25} | {'模板名称':<40} | {'工艺代码':<10} | {'工艺名称':<20}")
        print("-" * 100)
        
        count = 0
        for row in result:
            print(f"{row[0]:<25} | {row[1]:<40} | {row[2]:<10} | {row[3]:<20}")
            count += 1
        
        print("-" * 100)
        print(f"总计: {count} 个系统模板")
        print("=" * 100)
        
        # 查询模板总数
        total_result = conn.execute(text("SELECT COUNT(*) FROM wps_templates"))
        total = total_result.scalar()
        print(f"\n数据库中总共有 {total} 个模板（包括系统模板和用户模板）\n")

if __name__ == "__main__":
    check_templates()

