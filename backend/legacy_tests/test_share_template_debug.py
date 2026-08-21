#!/usr/bin/env python3
"""
测试分享模板API的详细调试脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from app.core.database import get_db
from app.models.user import User
from app.models.wps_template import WPSTemplate
from app.core.security import create_access_token

def test_share_template():
    """测试分享模板功能"""
    print("=== 开始测试分享模板功能 ===")

    # 1. 获取用户和token
    try:
        db = next(get_db())
        user = db.query(User).first()

        if not user:
            print("[ERROR] 未找到任何用户")
            return

        print(f"[OK] 找到用户: ID={user.id}, 用户名={user.username}")

        token = create_access_token(subject=str(user.id))
        print(f"[OK] 生成token: {token[:50]}...")

        # 2. 查找用户自己的模板
        from app.models.wps_template import WPSTemplate
        user_templates = db.query(WPSTemplate).filter(
            WPSTemplate.user_id == user.id
        ).all()

        print(f"[OK] 用户拥有的模板数量: {len(user_templates)}")

        if not user_templates:
            print("[ERROR] 用户没有自己的模板，创建一个测试模板...")
            # 创建一个测试模板
            import uuid

            test_template = WPSTemplate(
                id=str(uuid.uuid4()),
                name="测试分享模板",
                description="用于测试分享功能的模板",
                welding_process="SMAW",
                welding_process_name="焊条电弧焊",
                module_instances=[],
                user_id=user.id,
                workspace_type="personal",
                is_system=False,
                is_active=True
            )

            db.add(test_template)
            db.commit()
            db.refresh(test_template)

            print(f"[OK] 创建测试模板成功: ID={test_template.id}")
            template_to_share = test_template
        else:
            template_to_share = user_templates[0]
            print(f"[OK] 使用现有模板: ID={template_to_share.id}, 名称={template_to_share.name}")

        db.close()

        # 3. 准备分享数据
        share_data = {
            "original_template_id": template_to_share.id,
            "name": f"分享的模板 - {template_to_share.name}",
            "description": f"这是一个从 {template_to_share.name} 分享的模板",
            "welding_process": template_to_share.welding_process,
            "welding_process_name": template_to_share.welding_process_name,
            "module_instances": template_to_share.module_instances or [],
            "tags": ["测试", "调试"],
            "difficulty_level": "beginner",
            "changelog": "初始版本"
        }

        print(f"[OK] 准备分享数据: 模板ID={share_data['original_template_id']}")
        print(f"   分享名称: {share_data['name']}")
        print(f"   模块实例数量: {len(share_data['module_instances'])}")

        # 4. 发送分享请求
        url = "http://localhost:8000/api/v1/shared-library/templates/share"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        print(f"\n[SEND] 发送POST请求到: {url}")
        print(f"   Headers: {headers}")
        print(f"   Body: {json.dumps(share_data, ensure_ascii=False, indent=2)}")

        response = requests.post(url, headers=headers, json=share_data, timeout=30)

        print(f"\n[RECV] 收到响应:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")

        try:
            response_data = response.json()
            print(f"   响应体: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"   响应体 (原始): {response.text}")

        # 5. 分析结果
        if response.status_code == 200:
            print("[SUCCESS] 模板分享成功！")
        elif response.status_code == 404:
            print("[ERROR] 原始模板不存在或无权限访问")
        elif response.status_code == 400:
            print("[ERROR] 请求参数错误或模板已经分享过")
        elif response.status_code == 500:
            print("[ERROR] 服务器内部错误 - 请查看后端日志获取详细信息")
        else:
            print(f"[ERROR] 未知错误: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    test_share_template()