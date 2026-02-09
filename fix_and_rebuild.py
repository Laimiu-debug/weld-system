#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 Dockerfile 并重新构建"""

import paramiko
import os
import sys

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
    
    exit_status = stdout.channel.recv_exit_status()
    return exit_status, ''.join(output_lines)

def main():
    hostname = "43.142.188.252"
    username = "root"
    password = "Weld2024"
    key_file = "server-key.pem"
    project_dir = "/home/ubuntu/weld-system"
    
    print("=" * 60)
    print("🔧 修复 Dockerfile 并重新构建")
    print("=" * 60)
    
    try:
        # 连接服务器
        print(f"\n📡 连接服务器 {hostname}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            key_filename=key_file,
            timeout=30
        )
        print("✅ 连接成功！")
        
        # 1. 停止当前构建进程
        print("\n" + "=" * 60)
        print("步骤 1/5: 停止当前构建进程")
        print("=" * 60)
        execute_command(
            ssh,
            "pkill -f 'docker-compose build' || true",
            "",
            show_output=False
        )
        print("✅ 已停止构建进程")
        
        # 2. 停止所有容器
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose down",
            "步骤 2/5: 停止所有容器"
        )
        
        # 3. 上传修复后的 Dockerfile
        print("\n" + "=" * 60)
        print("步骤 3/5: 上传修复后的 Dockerfile")
        print("=" * 60)
        
        sftp = ssh.open_sftp()
        local_dockerfile = "backend/Dockerfile"
        remote_dockerfile = f"{project_dir}/backend/Dockerfile"
        
        print(f"📤 上传: {local_dockerfile} -> {remote_dockerfile}")
        sftp.put(local_dockerfile, remote_dockerfile)
        sftp.close()
        print("✅ Dockerfile 上传完成！")
        
        # 4. 只清理 backend 的构建缓存
        print("\n" + "=" * 60)
        print("步骤 4/5: 清理 backend 构建缓存")
        print("=" * 60)
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose rm -f backend",
            "",
            show_output=False
        )
        execute_command(
            ssh,
            "docker image rm -f weld-system-backend 2>/dev/null || true",
            "",
            show_output=False
        )
        print("✅ 已清理 backend 缓存")

        # 5. 只重新构建 backend
        print("\n" + "=" * 60)
        print("步骤 5/5: 重新构建 backend 镜像")
        print("=" * 60)
        print("🔨 开始构建 backend（这可能需要 10-20 分钟）...")
        print("提示: frontend 和 admin-portal 已构建成功，无需重新构建")
        print("提示: 正在安装系统依赖和 Python 包，请耐心等待...\n")

        # 只构建 backend，使用 --no-cache 确保使用新的 Dockerfile
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {project_dir} && docker-compose build --no-cache backend 2>&1",
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
            print("\n请检查上面的错误信息")
            ssh.close()
            sys.exit(1)
        
        print("\n✅ 构建完成！")
        
        # 6. 启动服务
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose up -d",
            "启动所有服务"
        )
        
        # 等待服务启动
        print("\n⏳ 等待服务启动...")
        import time
        time.sleep(10)
        
        # 7. 初始化数据库
        print("\n" + "=" * 60)
        print("初始化数据库")
        print("=" * 60)
        exit_code, output = execute_command(
            ssh,
            f"cd {project_dir} && docker-compose exec -T backend alembic upgrade head",
            ""
        )
        
        if exit_code != 0:
            print("⚠️  数据库迁移可能失败，但服务可能已经在运行")
        
        # 8. 检查服务状态
        execute_command(
            ssh,
            f"cd {project_dir} && docker-compose ps",
            "检查服务状态"
        )
        
        print("\n" + "=" * 60)
        print("🎉 部署完成！")
        print("=" * 60)
        print(f"\n访问地址：")
        print(f"  用户门户: http://{hostname}")
        print(f"  管理门户: http://{hostname}/admin")
        print(f"  API文档:  http://{hostname}/api/docs")
        print(f"  健康检查: http://{hostname}/api/v1/health")
        print("\n提示: 如果服务未正常启动，请等待几分钟后再访问")
        
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

