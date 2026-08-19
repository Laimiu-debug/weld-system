#!/usr/bin/env python3
"""
重新部署修复后的版本
"""
import subprocess
import sys
import time
import os

def run_command(cmd, description):
    """执行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    host = os.environ.get("WELD_SSH_HOST")
    if not host:
        raise RuntimeError("WELD_SSH_HOST is required")
    server = f"{os.environ.get('WELD_SSH_USER', 'deploy')}@{host}"
    key_file = os.environ.get("WELD_SSH_KEY")
    if not key_file:
        raise RuntimeError("WELD_SSH_KEY is required")
    
    steps = [
        # 1. 停止当前构建
        (
            f'ssh -i {key_file} {server} '
            f'"cd /home/ubuntu/weld-system && docker-compose down"',
            "停止当前服务"
        ),
        
        # 2. 上传修复后的 Dockerfile
        (
            f'scp -i {key_file} backend/Dockerfile {server}:/home/ubuntu/weld-system/backend/',
            "上传修复后的 Dockerfile"
        ),
        
        # 3. 清理旧的构建缓存
        (
            f'ssh -i {key_file} {server} '
            f'"docker builder prune -af"',
            "清理构建缓存"
        ),
        
        # 4. 重新构建（使用缓存）
        (
            f'ssh -i {key_file} {server} '
            f'"cd /home/ubuntu/weld-system && docker-compose build backend > .build.log 2>&1 &"',
            "启动后端构建（后台运行）"
        ),
    ]
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print(f"\n❌ 失败: {desc}")
            return False
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print("✅ 部署脚本执行完成！")
    print("📊 使用以下命令监控构建进度:")
    print(f"   python monitor_build.py")
    print(f"\n📋 查看构建日志:")
    print(f'   ssh -i {key_file} {server} "tail -f /home/ubuntu/weld-system/.build.log"')
    print(f"{'='*60}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

