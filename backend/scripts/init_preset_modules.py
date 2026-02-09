"""
初始化预设模块脚本
将PQR、pPQR和通用预设模块插入数据库
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.custom_module import CustomModule
from app.data.pqr_preset_modules import PQR_PRESET_MODULES
from app.data.ppqr_preset_modules import PPQR_PRESET_MODULES
from app.data.common_preset_modules import COMMON_PRESET_MODULES
from datetime import datetime
import uuid


def init_preset_modules(db: Session):
    """
    初始化所有预设模块
    """
    print("=" * 80)
    print("开始初始化预设模块")
    print("=" * 80)
    
    # 统计
    stats = {
        'pqr': {'total': 0, 'created': 0, 'skipped': 0},
        'ppqr': {'total': 0, 'created': 0, 'skipped': 0},
        'common': {'total': 0, 'created': 0, 'skipped': 0}
    }
    
    # 1. 初始化PQR预设模块
    print("\n" + "-" * 80)
    print("1. 初始化PQR预设模块")
    print("-" * 80)
    
    for module_data in PQR_PRESET_MODULES:
        stats['pqr']['total'] += 1
        module_id = module_data['id']
        
        # 检查是否已存在
        existing = db.query(CustomModule).filter(CustomModule.id == module_id).first()
        
        if existing:
            print(f"⊙ 跳过已存在的模块: {module_data['name']} ({module_id})")
            stats['pqr']['skipped'] += 1
            continue
        
        # 创建新模块
        module = CustomModule(
            id=module_id,
            name=module_data['name'],
            description=module_data['description'],
            icon=module_data['icon'],
            module_type=module_data['module_type'],
            category=module_data['category'],
            repeatable=module_data['repeatable'],
            workspace_type=module_data['workspace_type'],
            is_shared=module_data['is_shared'],
            access_level=module_data['access_level'],
            fields=module_data['fields'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(module)
        print(f"✓ 创建模块: {module_data['name']} ({module_id})")
        stats['pqr']['created'] += 1
    
    # 2. 初始化pPQR预设模块
    print("\n" + "-" * 80)
    print("2. 初始化pPQR预设模块")
    print("-" * 80)
    
    for module_data in PPQR_PRESET_MODULES:
        stats['ppqr']['total'] += 1
        module_id = module_data['id']
        
        # 检查是否已存在
        existing = db.query(CustomModule).filter(CustomModule.id == module_id).first()
        
        if existing:
            print(f"⊙ 跳过已存在的模块: {module_data['name']} ({module_id})")
            stats['ppqr']['skipped'] += 1
            continue
        
        # 创建新模块
        module = CustomModule(
            id=module_id,
            name=module_data['name'],
            description=module_data['description'],
            icon=module_data['icon'],
            module_type=module_data['module_type'],
            category=module_data['category'],
            repeatable=module_data['repeatable'],
            workspace_type=module_data['workspace_type'],
            is_shared=module_data['is_shared'],
            access_level=module_data['access_level'],
            fields=module_data['fields'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(module)
        print(f"✓ 创建模块: {module_data['name']} ({module_id})")
        stats['ppqr']['created'] += 1
    
    # 3. 初始化通用预设模块
    print("\n" + "-" * 80)
    print("3. 初始化通用预设模块")
    print("-" * 80)
    
    for module_data in COMMON_PRESET_MODULES:
        stats['common']['total'] += 1
        module_id = module_data['id']
        
        # 检查是否已存在
        existing = db.query(CustomModule).filter(CustomModule.id == module_id).first()
        
        if existing:
            print(f"⊙ 跳过已存在的模块: {module_data['name']} ({module_id})")
            stats['common']['skipped'] += 1
            continue
        
        # 创建新模块
        module = CustomModule(
            id=module_id,
            name=module_data['name'],
            description=module_data['description'],
            icon=module_data['icon'],
            module_type=module_data['module_type'],
            category=module_data['category'],
            repeatable=module_data['repeatable'],
            workspace_type=module_data['workspace_type'],
            is_shared=module_data['is_shared'],
            access_level=module_data['access_level'],
            fields=module_data['fields'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(module)
        print(f"✓ 创建模块: {module_data['name']} ({module_id})")
        stats['common']['created'] += 1
    
    # 提交事务
    try:
        db.commit()
        print("\n" + "=" * 80)
        print("✓ 所有模块已成功提交到数据库")
        print("=" * 80)
    except Exception as e:
        db.rollback()
        print("\n" + "=" * 80)
        print(f"✗ 提交失败: {e}")
        print("=" * 80)
        raise
    
    # 打印统计信息
    print("\n" + "=" * 80)
    print("初始化统计")
    print("=" * 80)
    print(f"\nPQR模块:")
    print(f"  总数: {stats['pqr']['total']}")
    print(f"  新建: {stats['pqr']['created']}")
    print(f"  跳过: {stats['pqr']['skipped']}")
    
    print(f"\npPQR模块:")
    print(f"  总数: {stats['ppqr']['total']}")
    print(f"  新建: {stats['ppqr']['created']}")
    print(f"  跳过: {stats['ppqr']['skipped']}")
    
    print(f"\n通用模块:")
    print(f"  总数: {stats['common']['total']}")
    print(f"  新建: {stats['common']['created']}")
    print(f"  跳过: {stats['common']['skipped']}")
    
    total_created = stats['pqr']['created'] + stats['ppqr']['created'] + stats['common']['created']
    total_skipped = stats['pqr']['skipped'] + stats['ppqr']['skipped'] + stats['common']['skipped']
    total_all = stats['pqr']['total'] + stats['ppqr']['total'] + stats['common']['total']
    
    print(f"\n总计:")
    print(f"  总数: {total_all}")
    print(f"  新建: {total_created}")
    print(f"  跳过: {total_skipped}")
    print("=" * 80)


def verify_modules(db: Session):
    """
    验证模块是否正确创建
    """
    print("\n" + "=" * 80)
    print("验证预设模块")
    print("=" * 80)
    
    # 按module_type统计
    for module_type in ['wps', 'pqr', 'ppqr', 'common']:
        count = db.query(CustomModule).filter(
            CustomModule.module_type == module_type,
            CustomModule.workspace_type == 'system'
        ).count()
        print(f"{module_type.upper()}模块数量: {count}")
    
    # 按category统计
    print("\n按分类统计:")
    categories = ['basic', 'parameters', 'materials', 'tests', 'results', 'equipment', 'attachments', 'notes']
    for category in categories:
        count = db.query(CustomModule).filter(
            CustomModule.category == category,
            CustomModule.workspace_type == 'system'
        ).count()
        if count > 0:
            print(f"  {category}: {count}")
    
    print("=" * 80)


def main():
    """
    主函数
    """
    print("\n" + "=" * 80)
    print("预设模块初始化脚本")
    print("=" * 80)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化预设模块
        init_preset_modules(db)
        
        # 验证
        verify_modules(db)
        
        print("\n✓✓✓ 初始化完成！")
        
    except Exception as e:
        print(f"\n✗✗✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

