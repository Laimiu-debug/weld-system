#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从本地上传并部署到服务器"""

import os
import sys
from pathlib import Path
import stat
from deployment_ssh import connect_ssh, load_ssh_config

def execute_command(ssh, command, description="", show_output=True):
    """执行SSH命令并显示输出"""
    if description:
        print("\n" + "=" * 60)
        print(f"{description}")
        print("=" * 60)
    
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    output_lines = []
    while True:
        line = stdout.readline()
        if not line:
            break
        if show_output:
            print(line, end='')
        output_lines.append(line)
    
    return stdout.channel.recv_exit_status(), ''.join(output_lines)

def upload_directory(sftp, local_path, remote_path, exclude_patterns):
    """递归上传目录"""
    
    # 确保远程目录存在
    try:
        sftp.stat(remote_path)
    except:
        try:
            sftp.mkdir(remote_path)
        except:
            pass
    
    for item in os.listdir(local_path):
        # 检查是否应该排除
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern.startswith('*'):
                if item.endswith(pattern[1:]):
                    should_exclude = True
                    break
            elif item == pattern:
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        local_item = os.path.join(local_path, item)
        remote_item = f"{remote_path}/{item}"
        
        if os.path.isfile(local_item):
            print(f"📤 上传: {item}")
            try:
                sftp.put(local_item, remote_item)
                # 如果是.sh文件，设置执行权限
                if item.endswith('.sh'):
                    sftp.chmod(remote_item, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            except Exception as e:
                print(f"  ⚠️  上传失败: {e}")
        elif os.path.isdir(local_item):
            print(f"📁 目录: {item}/")
            upload_directory(sftp, local_item, remote_item, exclude_patterns)

def main():
    config = load_ssh_config()
    hostname = config.host
    project_dir = config.project_dir
    
    print("=" * 60)
    print("🚀 从本地上传并部署到服务器")
    print("=" * 60)
    
    try:
        # 连接服务器
        print(f"\n📡 连接服务器 {hostname}...")
        ssh = connect_ssh(config)
        print("✅ 连接成功！")
        
        # 1. 停止所有容器
        execute_command(
            ssh,
            f"cd {project_dir} 2>/dev/null && docker-compose down -v 2>/dev/null || true",
            "步骤 1/7: 停止所有容器"
        )
        
        # 2. 清理Docker资源
        execute_command(
            ssh,
            "docker system prune -af --volumes",
            "步骤 2/7: 清理Docker资源"
        )
        
        # 3. 删除旧项目目录
        execute_command(
            ssh,
            f"rm -rf {project_dir}",
            "步骤 3/7: 删除旧项目目录"
        )
        
        # 4. 创建新项目目录
        execute_command(
            ssh,
            f"mkdir -p {project_dir}",
            "步骤 4/7: 创建新项目目录"
        )
        
        # 5. 上传文件
        print("\n" + "=" * 60)
        print("步骤 5/7: 上传项目文件")
        print("=" * 60)
        
        local_dir = os.getcwd()
        
        # 需要排除的文件和目录
        exclude_patterns = [
            'node_modules',
            '__pycache__',
            '*.pyc',
            '.git',
            'dist',
            'build',
            '.vscode',
            '.idea',
            '*.log',
            '.env.local',
            'venv',
            '.pytest_cache',
            'server-key.pem',
            '.gitignore',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        sftp = ssh.open_sftp()
        print(f"开始上传 {local_dir} 到 {project_dir}...\n")
        upload_directory(sftp, local_dir, project_dir, exclude_patterns)
        sftp.close()
        print("\n✅ 文件上传完成！")
        
        # 6. 修复Git权限
        execute_command(
            ssh,
            f"git config --global --add safe.directory {project_dir}",
            "步骤 6/7: 配置Git权限",
            show_output=False
        )
        
        # 7. 构建并启动
        print("\n" + "=" * 60)
        print("步骤 7/7: 构建并启动服务")
        print("=" * 60)
        print("🔨 开始构建Docker镜像（这可能需要较长时间）...")
        print("提示: 如果下载速度慢，请耐心等待...\n")
        
        # 构建镜像
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {project_dir} && docker-compose build --no-cache 2>&1",
            get_pty=True
        )
        
        # 实时显示构建输出
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line, end='')
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            print("\n❌ 构建失败！")
            ssh.close()
            sys.exit(1)
        
        print("\n✅ 构建完成！")
        
        # 启动服务
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose up -d",
            "启动所有服务"
        )
        
        # 等待服务启动
        print("\n⏳ 等待服务启动...")
        import time
        time.sleep(10)
        
        # 初始化数据库
        print("\n" + "=" * 60)
        print("初始化数据库")
        print("=" * 60)
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose exec -T backend alembic upgrade head",
            ""
        )
        
        # 检查服务状态
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose ps",
            "检查服务状态"
        )
        
        print("\n" + "=" * 60)
        print("🎉 部署完成！")
        print("=" * 60)
        print(f"\n访问地址：")
        print(f"  用户门户: http://{hostname}:3000")
        print(f"  管理门户: http://{hostname}:3001")
        print(f"  API文档:  http://{hostname}:8000/docs")
        print(f"  健康检查: http://{hostname}:8000/api/v1/health")
        
        ssh.close()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

