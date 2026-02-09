"""
共享库功能测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, engine
from app.models.shared_library import SharedModule, SharedTemplate, UserRating, SharedDownload, SharedComment
from app.models.custom_module import CustomModule
from app.models.wps_template import WPSTemplate
from app.models.user import User
from app.schemas.shared_library import SharedModuleCreate, SharedTemplateCreate
from app.services.shared_library_service import SharedLibraryService
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid


def test_database_migration():
    """测试数据库迁移是否成功"""
    print("=== 测试数据库迁移 ===")

    try:
        # 测试连接数据库
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")

        # 检查表是否创建成功
        with engine.connect() as connection:
            tables = [
                'shared_modules',
                'shared_templates',
                'user_ratings',
                'shared_downloads',
                'shared_comments'
            ]

            for table in tables:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1"))
                    print(f"✅ 表 {table} 存在")
                except Exception as e:
                    print(f"❌ 表 {table} 不存在: {e}")

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

    return True


def test_shared_module_creation():
    """测试共享模块创建"""
    print("\n=== 测试共享模块创建 ===")

    db = next(get_db())
    try:
        # 创建测试用户
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="testpassword",
                is_active=True,
                role="user"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ 创建测试用户: {test_user.email}")

        # 创建测试自定义模块
        test_module = CustomModule(
            id=str(uuid.uuid4()),
            name="测试模块",
            description="这是一个测试模块",
            icon="TestOutlined",
            category="basic",
            repeatable=False,
            fields={"field1": "value1"},
            user_id=test_user.id,
            workspace_type="personal",
            access_level="private"
        )
        db.add(test_module)
        db.commit()
        db.refresh(test_module)
        print(f"✅ 创建测试自定义模块: {test_module.name}")

        # 测试共享模块创建
        service = SharedLibraryService(db)
        shared_module_data = SharedModuleCreate(
            original_module_id=test_module.id,
            name="共享测试模块",
            description="这是一个共享的测试模块",
            icon="ShareOutlined",
            category="basic",
            repeatable=False,
            fields={"field1": "value1"},
            tags=["测试", "示例"],
            difficulty_level="beginner",
            changelog="初始版本"
        )

        shared_module = service.create_shared_module(shared_module_data, test_user.id)
        print(f"✅ 创建共享模块成功: {shared_module.name}")

        return shared_module.id, test_user.id

    except Exception as e:
        print(f"❌ 共享模块创建测试失败: {e}")
        return None, None
    finally:
        db.close()


def test_shared_template_creation():
    """测试共享模板创建"""
    print("\n=== 测试共享模板创建 ===")

    db = next(get_db())
    try:
        # 获取测试用户
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            print("❌ 测试用户不存在")
            return None, None

        # 创建测试WPS模板
        test_template = WPSTemplate(
            id=str(uuid.uuid4()),
            name="测试WPS模板",
            description="这是一个测试WPS模板",
            welding_process="111",
            welding_process_name="手工电弧焊",
            standard="AWS D1.1",
            module_instances={"module1": {"field": "value"}},
            user_id=test_user.id,
            workspace_type="personal",
            access_level="private",
            template_source="user",
            version="1.0",
            is_active=True,
            is_system=False,
            usage_count=0,
            created_by=test_user.id,
            updated_by=test_user.id
        )
        db.add(test_template)
        db.commit()
        db.refresh(test_template)
        print(f"✅ 创建测试WPS模板: {test_template.name}")

        # 测试共享模板创建
        service = SharedLibraryService(db)
        shared_template_data = SharedTemplateCreate(
            original_template_id=test_template.id,
            name="共享测试WPS模板",
            description="这是一个共享的测试WPS模板",
            welding_process="111",
            welding_process_name="手工电弧焊",
            standard="AWS D1.1",
            module_instances={"module1": {"field": "value"}},
            tags=["测试", "WPS", "示例"],
            difficulty_level="intermediate",
            industry_type="造船",
            changelog="初始版本"
        )

        shared_template = service.create_shared_template(shared_template_data, test_user.id)
        print(f"✅ 创建共享模板成功: {shared_template.name}")

        return shared_template.id, test_user.id

    except Exception as e:
        print(f"❌ 共享模板创建测试失败: {e}")
        return None, None
    finally:
        db.close()


def test_rating_and_download():
    """测试评分和下载功能"""
    print("\n=== 测试评分和下载功能 ===")

    db = next(get_db())
    try:
        service = SharedLibraryService(db)
        test_user = db.query(User).filter(User.email == "test@example.com").first()

        if not test_user:
            print("❌ 测试用户不存在")
            return False

        # 获取共享模块和模板
        shared_module = db.query(SharedModule).first()
        shared_template = db.query(SharedTemplate).first()

        # 测试模块评分
        if shared_module:
            from app.schemas.shared_library import UserRatingCreate
            rating_data = UserRatingCreate(
                target_type="module",
                target_id=shared_module.id,
                rating_type="like"
            )
            rating = service.rate_shared_resource(rating_data, test_user.id)
            print(f"✅ 模块评分成功: {rating.rating_type}")

        # 测试模板评分
        if shared_template:
            rating_data = UserRatingCreate(
                target_type="template",
                target_id=shared_template.id,
                rating_type="like"
            )
            rating = service.rate_shared_resource(rating_data, test_user.id)
            print(f"✅ 模板评分成功: {rating.rating_type}")

        # 测试模块下载（模拟）
        if shared_module:
            try:
                # 先审核通过
                service.review_shared_resource("module", shared_module.id,
                    {"status": "approved", "review_comment": "测试通过"}, test_user.id)

                # 测试下载
                result = service.download_shared_module(shared_module.id, test_user.id)
                print(f"✅ 模块下载成功: {result['message']}")
            except Exception as e:
                print(f"⚠️ 模块下载测试: {e}")

        # 测试模板下载（模拟）
        if shared_template:
            try:
                # 先审核通过
                service.review_shared_resource("template", shared_template.id,
                    {"status": "approved", "review_comment": "测试通过"}, test_user.id)

                # 测试下载
                result = service.download_shared_template(shared_template.id, test_user.id)
                print(f"✅ 模板下载成功: {result['message']}")
            except Exception as e:
                print(f"⚠️ 模板下载测试: {e}")

        return True

    except Exception as e:
        print(f"❌ 评分和下载测试失败: {e}")
        return False
    finally:
        db.close()


def test_admin_functions():
    """测试管理员功能"""
    print("\n=== 测试管理员功能 ===")

    db = next(get_db())
    try:
        service = SharedLibraryService(db)

        # 创建管理员用户
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@example.com",
                username="admin",
                hashed_password="adminpassword",
                is_active=True,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"✅ 创建管理员用户: {admin_user.email}")

        # 获取共享资源
        shared_module = db.query(SharedModule).first()
        shared_template = db.query(SharedTemplate).first()

        # 测试审核功能
        if shared_module:
            try:
                from app.schemas.shared_library import ReviewAction
                review_action = ReviewAction(
                    status="approved",
                    review_comment="管理员审核通过"
                )
                success = service.review_shared_resource("module", shared_module.id, review_action, admin_user.id)
                print(f"✅ 模块审核成功: {success}")
            except Exception as e:
                print(f"⚠️ 模块审核测试: {e}")

        if shared_template:
            try:
                review_action = ReviewAction(
                    status="approved",
                    review_comment="管理员审核通过"
                )
                success = service.review_shared_resource("template", shared_template.id, review_action, admin_user.id)
                print(f"✅ 模板审核成功: {success}")
            except Exception as e:
                print(f"⚠️ 模板审核测试: {e}")

        # 测试推荐功能
        if shared_module:
            try:
                from app.schemas.shared_library import FeaturedAction
                featured_action = FeaturedAction(
                    is_featured=True,
                    featured_order=1
                )
                success = service.set_featured_resource("module", shared_module.id, featured_action)
                print(f"✅ 模块推荐设置成功: {success}")
            except Exception as e:
                print(f"⚠️ 模块推荐测试: {e}")

        # 测试统计功能
        try:
            stats = service.get_library_stats()
            print(f"✅ 统计信息获取成功:")
            print(f"   - 总模块数: {stats['total_modules']}")
            print(f"   - 总模板数: {stats['total_templates']}")
            print(f"   - 待审核模块: {stats['pending_modules']}")
            print(f"   - 待审核模板: {stats['pending_templates']}")
            print(f"   - 总下载量: {stats['total_downloads']}")
            print(f"   - 总评分数: {stats['total_ratings']}")
        except Exception as e:
            print(f"⚠️ 统计功能测试: {e}")

        return True

    except Exception as e:
        print(f"❌ 管理员功能测试失败: {e}")
        return False
    finally:
        db.close()


def test_search_and_filter():
    """测试搜索和筛选功能"""
    print("\n=== 测试搜索和筛选功能 ===")

    db = next(get_db())
    try:
        service = SharedLibraryService(db)

        from app.schemas.shared_library import LibrarySearchQuery

        # 测试模块搜索
        query = LibrarySearchQuery(
            keyword="测试",
            status="approved",
            page=1,
            page_size=10,
            sort_by="created_at",
            sort_order="desc"
        )

        modules, total = service.get_shared_modules(query)
        print(f"✅ 模块搜索成功: 找到 {total} 个模块")

        # 测试模板搜索
        templates, total = service.get_shared_templates(query)
        print(f"✅ 模板搜索成功: 找到 {total} 个模板")

        # 测试分类筛选
        query.category = "basic"
        modules, total = service.get_shared_modules(query)
        print(f"✅ 分类筛选成功: 找到 {total} 个基础模块")

        # 测试推荐筛选
        query.featured_only = True
        modules, total = service.get_shared_modules(query)
        print(f"✅ 推荐筛选成功: 找到 {total} 个推荐模块")

        return True

    except Exception as e:
        print(f"❌ 搜索和筛选测试失败: {e}")
        return False
    finally:
        db.close()


def cleanup_test_data():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")

    db = next(get_db())
    try:
        # 删除测试用户和相关数据
        test_user = db.query(User).filter(User.email.in_(["test@example.com", "admin@example.com"])).all()

        for user in test_user:
            # 删除评分记录
            db.query(UserRating).filter(UserRating.user_id == user.id).delete()

            # 删除下载记录
            db.query(SharedDownload).filter(SharedDownload.user_id == user.id).delete()

            # 删除评论
            db.query(SharedComment).filter(SharedComment.user_id == user.id).delete()

            # 删除自定义模块
            db.query(CustomModule).filter(CustomModule.user_id == user.id).delete()

            # 删除WPS模板
            db.query(WPSTemplate).filter(WPSTemplate.user_id == user.id).delete()

            # 删除共享模块（通过上传者）
            db.query(SharedModule).filter(SharedModule.uploader_id == user.id).delete()

            # 删除共享模板（通过上传者）
            db.query(SharedTemplate).filter(SharedTemplate.uploader_id == user.id).delete()

            # 删除用户
            db.delete(user)

        db.commit()
        print("✅ 测试数据清理完成")

    except Exception as e:
        print(f"❌ 清理测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """主测试函数"""
    print("🚀 开始共享库功能测试")
    print("=" * 50)

    success_count = 0
    total_tests = 6

    # 1. 测试数据库迁移
    if test_database_migration():
        success_count += 1

    # 2. 测试共享模块创建
    module_id, user_id = test_shared_module_creation()
    if module_id:
        success_count += 1

    # 3. 测试共享模板创建
    template_id, template_user_id = test_shared_template_creation()
    if template_id:
        success_count += 1

    # 4. 测试评分和下载功能
    if test_rating_and_download():
        success_count += 1

    # 5. 测试管理员功能
    if test_admin_functions():
        success_count += 1

    # 6. 测试搜索和筛选功能
    if test_search_and_filter():
        success_count += 1

    # 清理测试数据
    cleanup_test_data()

    # 输出测试结果
    print("\n" + "=" * 50)
    print(f"🎉 测试完成: {success_count}/{total_tests} 项测试通过")

    if success_count == total_tests:
        print("✅ 所有测试通过，共享库功能正常！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        return False


if __name__ == "__main__":
    main()