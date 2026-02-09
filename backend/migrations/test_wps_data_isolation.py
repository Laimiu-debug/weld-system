"""
测试 WPS 数据隔离

验证以下场景：
1. 个人工作区 - 同一用户不能创建重复编号 ✗
2. 个人工作区 - 不同用户可以创建相同编号 ✓
3. 企业工作区 - 同一企业不能创建重复编号 ✗
4. 企业工作区 - 不同企业可以创建相同编号 ✓
5. 个人工作区和企业工作区可以有相同编号 ✓
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def test_data_isolation():
    print("=" * 60)
    print("测试 WPS 数据隔离")
    print("=" * 60)

    engine = create_engine(str(settings.DATABASE_URL))

    with engine.connect() as conn:
        # 获取真实的用户和企业 ID
        print("\n获取测试数据...")

        # 获取两个用户
        result = conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 2"))
        users = [row[0] for row in result]

        if len(users) < 2:
            print("✗ 数据库中用户数量不足（需要至少 2 个用户）")
            return

        user1_id, user2_id = users[0], users[1]
        print(f"✓ 使用用户: user1_id={user1_id}, user2_id={user2_id}")

        # 获取两个企业
        result = conn.execute(text("SELECT id FROM companies ORDER BY id LIMIT 2"))
        companies = [row[0] for row in result]

        if len(companies) < 2:
            print("✗ 数据库中企业数量不足（需要至少 2 个企业）")
            print("提示：可以使用真实用户和企业进行测试，或者跳过企业工作区测试")
            company1_id, company2_id = None, None
        else:
            company1_id, company2_id = companies[0], companies[1]
            print(f"✓ 使用企业: company1_id={company1_id}, company2_id={company2_id}")

        # 清理测试数据
        print("\n清理旧的测试数据...")
        conn.execute(text("DELETE FROM wps WHERE title LIKE 'Test WPS%'"))
        conn.commit()
        print("✓ 清理完成")
        
        # 测试 1: 个人工作区 - 同一用户不能创建重复编号
        print("\n" + "=" * 60)
        print("测试 1: 个人工作区 - 同一用户不能创建重复编号")
        print("=" * 60)
        
        try:
            # 创建第一个 WPS
            conn.execute(text(f"""
                INSERT INTO wps (user_id, workspace_type, wps_number, title, created_by, created_at, updated_at)
                VALUES ({user1_id}, 'personal', 'WPS-TEST-001', 'Test WPS 1', {user1_id}, NOW(), NOW())
            """))
            conn.commit()
            print(f"✓ 创建第一个 WPS 成功: user_id={user1_id}, wps_number=WPS-TEST-001")

            # 尝试创建重复编号的 WPS（应该失败）
            try:
                conn.execute(text(f"""
                    INSERT INTO wps (user_id, workspace_type, wps_number, title, created_by, created_at, updated_at)
                    VALUES ({user1_id}, 'personal', 'WPS-TEST-001', 'Test WPS 2', {user1_id}, NOW(), NOW())
                """))
                conn.commit()
                print("✗ 测试失败：允许创建重复编号（不应该）")
            except Exception as e:
                conn.rollback()
                print(f"✓ 测试通过：正确阻止重复编号 ({str(e)[:80]}...)")
        except Exception as e:
            conn.rollback()
            print(f"✗ 测试失败: {e}")
        
        # 测试 2: 个人工作区 - 不同用户可以创建相同编号
        print("\n" + "=" * 60)
        print("测试 2: 个人工作区 - 不同用户可以创建相同编号")
        print("=" * 60)
        
        try:
            conn.execute(text(f"""
                INSERT INTO wps (user_id, workspace_type, wps_number, title, created_by, created_at, updated_at)
                VALUES ({user2_id}, 'personal', 'WPS-TEST-001', 'Test WPS 3', {user2_id}, NOW(), NOW())
            """))
            conn.commit()
            print(f"✓ 测试通过：不同用户可以使用相同编号 (user_id={user2_id}, wps_number=WPS-TEST-001)")
        except Exception as e:
            conn.rollback()
            print(f"✗ 测试失败：不允许不同用户使用相同编号 ({e})")
        
        # 测试 3: 企业工作区 - 同一企业不能创建重复编号
        print("\n" + "=" * 60)
        print("测试 3: 企业工作区 - 同一企业不能创建重复编号")
        print("=" * 60)

        if company1_id is None:
            print("⊘ 跳过测试：没有可用的企业数据")
        else:
            try:
                # 创建第一个企业 WPS
                conn.execute(text(f"""
                    INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by, created_at, updated_at)
                    VALUES ({user1_id}, 'enterprise', {company1_id}, 'WPS-TEST-002', 'Test WPS 4', {user1_id}, NOW(), NOW())
                """))
                conn.commit()
                print(f"✓ 创建第一个企业 WPS 成功: company_id={company1_id}, wps_number=WPS-TEST-002")

                # 尝试在同一企业创建重复编号（应该失败）
                try:
                    conn.execute(text(f"""
                        INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by, created_at, updated_at)
                        VALUES ({user2_id}, 'enterprise', {company1_id}, 'WPS-TEST-002', 'Test WPS 5', {user2_id}, NOW(), NOW())
                    """))
                    conn.commit()
                    print("✗ 测试失败：允许同一企业创建重复编号（不应该）")
                except Exception as e:
                    conn.rollback()
                    print(f"✓ 测试通过：正确阻止同一企业的重复编号 ({str(e)[:80]}...)")
            except Exception as e:
                conn.rollback()
                print(f"✗ 测试失败: {e}")
        
        # 测试 4: 企业工作区 - 不同企业可以创建相同编号
        print("\n" + "=" * 60)
        print("测试 4: 企业工作区 - 不同企业可以创建相同编号")
        print("=" * 60)

        if company2_id is None:
            print("⊘ 跳过测试：没有可用的企业数据")
        else:
            try:
                conn.execute(text(f"""
                    INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by, created_at, updated_at)
                    VALUES ({user1_id}, 'enterprise', {company2_id}, 'WPS-TEST-002', 'Test WPS 6', {user1_id}, NOW(), NOW())
                """))
                conn.commit()
                print(f"✓ 测试通过：不同企业可以使用相同编号 (company_id={company2_id}, wps_number=WPS-TEST-002)")
            except Exception as e:
                conn.rollback()
                print(f"✗ 测试失败：不允许不同企业使用相同编号 ({e})")
        
        # 测试 5: 个人工作区和企业工作区可以有相同编号
        print("\n" + "=" * 60)
        print("测试 5: 个人工作区和企业工作区可以有相同编号")
        print("=" * 60)

        if company1_id is None:
            print("⊘ 跳过测试：没有可用的企业数据")
        else:
            try:
                # 个人工作区已经有 WPS-TEST-001
                # 尝试在企业工作区创建相同编号
                conn.execute(text(f"""
                    INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by, created_at, updated_at)
                    VALUES ({user1_id}, 'enterprise', {company1_id}, 'WPS-TEST-001', 'Test WPS 7', {user1_id}, NOW(), NOW())
                """))
                conn.commit()
                print("✓ 测试通过：个人工作区和企业工作区可以使用相同编号 (wps_number=WPS-TEST-001)")
            except Exception as e:
                conn.rollback()
                print(f"✗ 测试失败：不允许个人和企业工作区使用相同编号 ({e})")
        
        # 查询所有测试数据
        print("\n" + "=" * 60)
        print("所有测试数据：")
        print("=" * 60)
        
        result = conn.execute(text("""
            SELECT id, user_id, workspace_type, company_id, wps_number, title
            FROM wps
            WHERE title LIKE 'Test WPS%'
            ORDER BY id
        """))
        
        print(f"{'ID':<5} {'User':<6} {'Workspace':<12} {'Company':<8} {'WPS Number':<15} {'Title':<15}")
        print("-" * 70)
        for row in result:
            company_id = row[3] if row[3] else 'NULL'
            print(f"{row[0]:<5} {row[1]:<6} {row[2]:<12} {company_id:<8} {row[4]:<15} {row[5]:<15}")
        
        # 清理测试数据
        print("\n清理测试数据...")
        conn.execute(text("DELETE FROM wps WHERE title LIKE 'Test WPS%'"))
        conn.commit()
        print("✓ 清理完成")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_data_isolation()

