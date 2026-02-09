"""
修复设备表中的 workspace_type 字段

这个脚本用于修复现有设备数据的 workspace_type 字段：
1. 检查所有设备的 workspace_type 字段
2. 如果 workspace_type 为 NULL 或空，根据 company_id 自动设置：
   - 如果 company_id 不为空 -> workspace_type = 'enterprise'
   - 如果 company_id 为空 -> workspace_type = 'personal'
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.equipment import Equipment
from app.core.database import SessionLocal

def fix_equipment_workspace_type():
    """修复设备的 workspace_type 字段"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("开始检查设备数据...")
        print("=" * 60)
        
        # 查询所有设备
        all_equipment = db.query(Equipment).all()
        print(f"\n总共找到 {len(all_equipment)} 个设备")
        
        if len(all_equipment) == 0:
            print("没有设备需要处理")
            return
        
        # 统计需要修复的设备
        need_fix = []
        personal_count = 0
        enterprise_count = 0
        
        print("\n设备详情：")
        print("-" * 60)
        
        for equipment in all_equipment:
            print(f"\n设备ID: {equipment.id}")
            print(f"  设备编号: {equipment.equipment_code}")
            print(f"  设备名称: {equipment.equipment_name}")
            print(f"  用户ID: {equipment.user_id}")
            print(f"  公司ID: {equipment.company_id}")
            print(f"  当前 workspace_type: {equipment.workspace_type}")
            
            # 检查是否需要修复
            if not equipment.workspace_type or equipment.workspace_type.strip() == '':
                need_fix.append(equipment)
                
                # 根据 company_id 判断应该设置的 workspace_type
                if equipment.company_id:
                    suggested_type = 'enterprise'
                    enterprise_count += 1
                else:
                    suggested_type = 'personal'
                    personal_count += 1
                
                print(f"  ⚠️  需要修复 -> 建议设置为: {suggested_type}")
            else:
                print(f"  ✓ 无需修复")
        
        print("\n" + "=" * 60)
        print(f"需要修复的设备数量: {len(need_fix)}")
        print(f"  - 应设置为 personal: {personal_count}")
        print(f"  - 应设置为 enterprise: {enterprise_count}")
        print("=" * 60)
        
        if len(need_fix) == 0:
            print("\n所有设备的 workspace_type 都已正确设置！")
            return
        
        # 询问是否执行修复
        print("\n是否执行修复？(y/n): ", end='')
        choice = input().strip().lower()
        
        if choice != 'y':
            print("取消修复操作")
            return
        
        # 执行修复
        print("\n开始修复...")
        fixed_count = 0
        
        for equipment in need_fix:
            old_type = equipment.workspace_type
            
            # 根据 company_id 设置 workspace_type
            if equipment.company_id:
                equipment.workspace_type = 'enterprise'
            else:
                equipment.workspace_type = 'personal'
            
            db.add(equipment)
            fixed_count += 1
            
            print(f"✓ 设备 {equipment.equipment_code} ({equipment.id}): "
                  f"{old_type or 'NULL'} -> {equipment.workspace_type}")
        
        # 提交更改
        db.commit()
        
        print("\n" + "=" * 60)
        print(f"修复完成！共修复 {fixed_count} 个设备")
        print("=" * 60)
        
        # 验证修复结果
        print("\n验证修复结果...")
        all_equipment = db.query(Equipment).all()
        
        personal_equipment = [e for e in all_equipment if e.workspace_type == 'personal']
        enterprise_equipment = [e for e in all_equipment if e.workspace_type == 'enterprise']
        invalid_equipment = [e for e in all_equipment if not e.workspace_type or e.workspace_type.strip() == '']
        
        print(f"\n当前设备统计：")
        print(f"  - 个人设备 (personal): {len(personal_equipment)}")
        print(f"  - 企业设备 (enterprise): {len(enterprise_equipment)}")
        print(f"  - 无效设备 (NULL/空): {len(invalid_equipment)}")
        
        if len(invalid_equipment) > 0:
            print("\n⚠️  警告：仍有设备的 workspace_type 无效！")
            for e in invalid_equipment:
                print(f"  - 设备ID {e.id}: {e.equipment_code}")
        else:
            print("\n✓ 所有设备的 workspace_type 都已正确设置！")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def show_current_status():
    """显示当前设备状态（不修复）"""
    
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("当前设备状态")
        print("=" * 60)
        
        all_equipment = db.query(Equipment).all()
        print(f"\n总设备数: {len(all_equipment)}")
        
        if len(all_equipment) == 0:
            print("没有设备")
            return
        
        personal_equipment = [e for e in all_equipment if e.workspace_type == 'personal']
        enterprise_equipment = [e for e in all_equipment if e.workspace_type == 'enterprise']
        invalid_equipment = [e for e in all_equipment if not e.workspace_type or e.workspace_type.strip() == '']
        
        print(f"\n按工作区类型分类：")
        print(f"  - 个人设备 (personal): {len(personal_equipment)}")
        print(f"  - 企业设备 (enterprise): {len(enterprise_equipment)}")
        print(f"  - 无效设备 (NULL/空): {len(invalid_equipment)}")
        
        if len(invalid_equipment) > 0:
            print(f"\n⚠️  发现 {len(invalid_equipment)} 个设备的 workspace_type 无效：")
            for e in invalid_equipment:
                print(f"  - ID: {e.id}, 编号: {e.equipment_code}, 名称: {e.equipment_name}")
                print(f"    用户ID: {e.user_id}, 公司ID: {e.company_id}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='修复设备表中的 workspace_type 字段')
    parser.add_argument('--status', action='store_true', help='只显示当前状态，不执行修复')
    parser.add_argument('--fix', action='store_true', help='执行修复操作')
    
    args = parser.parse_args()
    
    if args.status:
        show_current_status()
    elif args.fix:
        fix_equipment_workspace_type()
    else:
        # 默认显示状态
        print("使用方法：")
        print("  python fix_equipment_workspace_type.py --status  # 查看当前状态")
        print("  python fix_equipment_workspace_type.py --fix     # 执行修复")
        print()
        show_current_status()

