#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地构建测试脚本 - 在部署前验证 Docker 镜像构建"""

import subprocess
import sys
import time
from datetime import datetime

def run_command(command, description="", show_output=True):
    """运行命令并显示输出"""
    if description:
        print("\n" + "=" * 60)
        print(f"📋 {description}")
        print("=" * 60)
    
    print(f"💻 执行命令: {command}\n")
    
    start_time = time.time()
    
    try:
        if show_output:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            for line in process.stdout:
                print(line, end='')
            
            process.wait()
            return_code = process.returncode
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            return_code = result.returncode
            if return_code != 0:
                print(result.stderr)
        
        elapsed_time = time.time() - start_time
        
        if return_code == 0:
            print(f"\n✅ 成功！耗时: {elapsed_time:.2f} 秒")
            return True
        else:
            print(f"\n❌ 失败！返回码: {return_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False

def check_docker():
    """检查 Docker 是否运行"""
    print("\n" + "=" * 60)
    print("🔍 检查 Docker 环境")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            "docker --version",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"✅ Docker 版本: {result.stdout.strip()}")
        else:
            print("❌ Docker 未安装")
            return False
        
        result = subprocess.run(
            "docker ps",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print("✅ Docker 服务正在运行")
            return True
        else:
            print("❌ Docker 服务未启动，请先启动 Docker Desktop")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def get_image_size(image_name):
    """获取镜像大小"""
    try:
        result = subprocess.run(
            f'docker images {image_name} --format "{{{{.Size}}}}"',
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "未知"
    except:
        return "未知"

def main():
    print("=" * 60)
    print("🧪 本地 Docker 构建测试")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查 Docker
    if not check_docker():
        print("\n⚠️  请先启动 Docker Desktop，然后重新运行此脚本")
        sys.exit(1)
    
    # 2. 清理旧的测试镜像和容器
    print("\n" + "=" * 60)
    print("🧹 清理旧的测试资源")
    print("=" * 60)
    
    run_command(
        "docker stop backend-test 2>nul || echo 容器不存在",
        show_output=False
    )
    run_command(
        "docker rm backend-test 2>nul || echo 容器不存在",
        show_output=False
    )
    run_command(
        "docker rmi weld-backend-test 2>nul || echo 镜像不存在",
        show_output=False
    )
    
    print("✅ 清理完成")
    
    # 3. 构建 Backend 镜像
    build_start = time.time()
    
    success = run_command(
        "docker build -t weld-backend-test:latest -f backend/Dockerfile backend",
        "步骤 1/3: 构建 Backend 镜像"
    )
    
    if not success:
        print("\n❌ Backend 镜像构建失败！")
        print("\n💡 可能的原因：")
        print("   1. Docker Desktop 未启动")
        print("   2. 网络连接问题")
        print("   3. Dockerfile 语法错误")
        print("   4. 磁盘空间不足")
        sys.exit(1)
    
    build_time = time.time() - build_start
    
    # 4. 检查镜像信息
    print("\n" + "=" * 60)
    print("📊 镜像信息")
    print("=" * 60)
    
    image_size = get_image_size("weld-backend-test")
    print(f"镜像名称: weld-backend-test:latest")
    print(f"镜像大小: {image_size}")
    print(f"构建时间: {build_time:.2f} 秒 ({build_time/60:.2f} 分钟)")
    
    # 5. 测试运行容器（不需要数据库连接）
    print("\n" + "=" * 60)
    print("🚀 步骤 2/3: 测试运行容器")
    print("=" * 60)
    print("⚠️  注意: 容器会因为缺少数据库连接而失败，这是正常的")
    print("我们只是测试镜像是否可以启动\n")
    
    success = run_command(
        "docker run -d --name backend-test "
        "-e DATABASE_URL=postgresql://test:test@localhost:5432/test "
        "-e REDIS_URL=redis://localhost:6379/0 "
        "-e SECRET_KEY=test-secret-key "
        "-p 8001:8000 "
        "weld-backend-test:latest",
        show_output=False
    )
    
    if success:
        print("✅ 容器启动命令执行成功")
        
        # 等待容器启动
        print("\n⏳ 等待容器启动...")
        time.sleep(3)
        
        # 检查容器状态
        result = subprocess.run(
            "docker ps -a --filter name=backend-test --format \"{{.Status}}\"",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            status = result.stdout.strip()
            print(f"容器状态: {status}")
            
            # 查看容器日志
            print("\n📋 容器日志（最后 20 行）:")
            print("-" * 60)
            subprocess.run(
                "docker logs --tail 20 backend-test",
                shell=True
            )
            print("-" * 60)
    
    # 6. 清理测试资源
    print("\n" + "=" * 60)
    print("🧹 步骤 3/3: 清理测试资源")
    print("=" * 60)
    
    run_command("docker stop backend-test", show_output=False)
    run_command("docker rm backend-test", show_output=False)
    
    print("✅ 测试资源已清理")
    
    # 7. 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"✅ Backend 镜像构建成功")
    print(f"✅ 镜像大小: {image_size}")
    print(f"✅ 构建时间: {build_time:.2f} 秒 ({build_time/60:.2f} 分钟)")
    print(f"✅ 镜像已保存: weld-backend-test:latest")
    
    print("\n" + "=" * 60)
    print("🎉 本地测试完成！")
    print("=" * 60)
    
    print("\n💡 下一步操作：")
    print("   1. 如果构建成功，可以部署到服务器")
    print("   2. 运行: python deploy_from_local.py")
    print("   3. 或者使用 docker-compose 完整测试:")
    print("      docker-compose build")
    print("      docker-compose up -d")
    
    print("\n📝 保留测试镜像供参考，如需删除请运行:")
    print("   docker rmi weld-backend-test:latest")
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

