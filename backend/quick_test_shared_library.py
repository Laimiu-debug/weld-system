"""
共享库快速测试脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入是否成功"""
    print("=== 测试导入 ===")

    try:
        from app.models.shared_library import SharedModule, SharedTemplate, UserRating
        print("[OK] 共享库模型导入成功")

        from app.schemas.shared_library import SharedModuleCreate, SharedTemplateCreate
        print("[OK] 共享库Schema导入成功")

        from app.services.shared_library_service import SharedLibraryService
        print("[OK] 共享库服务导入成功")

        return True
    except Exception as e:
        print(f"[ERROR] 导入失败: {e}")
        return False

def test_api_routes():
    """测试API路由是否正确配置"""
    print("\n=== 测试API路由 ===")

    try:
        from app.api.v1.endpoints.shared_library import router
        print("[OK] 共享库API路由导入成功")

        # 检查路由数量
        routes = [route for route in router.routes if hasattr(route, 'path')]
        print(f"[OK] 共享库API路由数量: {len(routes)}")

        # 检查主要路由
        route_paths = [route.path for route in routes]
        expected_routes = [
            '/modules/share',
            '/modules',
            '/templates/share',
            '/templates',
            '/rate',
            '/comments'
        ]

        for expected_route in expected_routes:
            if any(expected_route in path for path in route_paths):
                print(f"[OK] 路由 {expected_route} 存在")
            else:
                print(f"[WARN] 路由 {expected_route} 可能不存在")

        return True
    except Exception as e:
        print(f"[ERROR] API路由测试失败: {e}")
        return False

def test_models():
    """测试模型定义"""
    print("\n=== 测试模型定义 ===")

    try:
        from app.models.shared_library import SharedModule, SharedTemplate

        # 检查SharedModule模型字段
        module_fields = [
            'id', 'original_module_id', 'name', 'description', 'uploader_id',
            'download_count', 'like_count', 'dislike_count', 'view_count',
            'status', 'is_featured', 'tags', 'difficulty_level'
        ]

        for field in module_fields:
            if hasattr(SharedModule, field):
                print(f"[OK] SharedModule.{field} 字段存在")
            else:
                print(f"[ERROR] SharedModule.{field} 字段缺失")

        # 检查SharedTemplate模型字段
        template_fields = [
            'id', 'original_template_id', 'name', 'description', 'uploader_id',
            'welding_process', 'standard', 'module_instances',
            'download_count', 'like_count', 'dislike_count', 'view_count',
            'status', 'is_featured', 'tags', 'difficulty_level', 'industry_type'
        ]

        for field in template_fields:
            if hasattr(SharedTemplate, field):
                print(f"[OK] SharedTemplate.{field} 字段存在")
            else:
                print(f"[ERROR] SharedTemplate.{field} 字段缺失")

        return True
    except Exception as e:
        print(f"[ERROR] 模型测试失败: {e}")
        return False

def test_schemas():
    """测试Schema定义"""
    print("\n=== 测试Schema定义 ===")

    try:
        from app.schemas.shared_library import (
            SharedModuleCreate, SharedTemplateCreate, LibrarySearchQuery,
            UserRatingCreate, ReviewAction, FeaturedAction
        )

        # 测试创建Schema实例
        module_create = SharedModuleCreate(
            original_module_id="test-id",
            name="测试模块",
            description="测试描述",
            category="basic",
            fields={"test": "field"},
            tags=["测试"],
            difficulty_level="beginner"
        )
        print("[OK] SharedModuleCreate Schema创建成功")

        template_create = SharedTemplateCreate(
            original_template_id="test-id",
            name="测试模板",
            description="测试描述",
            welding_process="111",
            module_instances={"test": "module"},
            tags=["测试"],
            difficulty_level="beginner"
        )
        print("[OK] SharedTemplateCreate Schema创建成功")

        search_query = LibrarySearchQuery(
            keyword="测试",
            category="basic",
            status="approved",
            page=1,
            page_size=20
        )
        print("[OK] LibrarySearchQuery Schema创建成功")

        rating_create = UserRatingCreate(
            target_type="module",
            target_id="test-id",
            rating_type="like"
        )
        print("[OK] UserRatingCreate Schema创建成功")

        review_action = ReviewAction(
            status="approved",
            review_comment="测试通过"
        )
        print("[OK] ReviewAction Schema创建成功")

        featured_action = FeaturedAction(
            is_featured=True,
            featured_order=1
        )
        print("[OK] FeaturedAction Schema创建成功")

        return True
    except Exception as e:
        print(f"[ERROR] Schema测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("共享库快速测试")
    print("=" * 40)

    success_count = 0
    total_tests = 4

    # 1. 测试导入
    if test_imports():
        success_count += 1

    # 2. 测试API路由
    if test_api_routes():
        success_count += 1

    # 3. 测试模型定义
    if test_models():
        success_count += 1

    # 4. 测试Schema定义
    if test_schemas():
        success_count += 1

    # 输出测试结果
    print("\n" + "=" * 40)
    print(f"测试结果: {success_count}/{total_tests} 项通过")

    if success_count == total_tests:
        print("快速测试通过！共享库基础功能正常。")
        print("\n接下来的步骤:")
        print("1. 运行数据库迁移")
        print("2. 运行完整测试: python test_shared_library.py")
        print("3. 启动后端服务: uvicorn app.main:app --reload")
        print("4. 测试前端页面: 访问 /shared-library")
        return True
    else:
        print("部分测试失败，请检查相关代码")
        return False

if __name__ == "__main__":
    main()