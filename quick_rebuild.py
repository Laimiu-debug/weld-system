#!/usr/bin/env python3
"""
快速重新构建 - 使用缓存
"""
import sys
import time
from deployment_ssh import connect_ssh, load_ssh_config

SSH_CONFIG = load_ssh_config()
SERVER_IP = SSH_CONFIG.host
PROJECT_DIR = SSH_CONFIG.project_dir

def execute_command(ssh, command, show_output=True):
    """执行命令并返回结果"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if show_output and output:
        print(output)
    if error and exit_code != 0:
        print(f"错误: {error}")
    
    return exit_code, output, error

def quick_rebuild():
    """快速重新构建"""
    print("=" * 60)
    print("🚀 快速重新构建 (使用缓存)")
    print("=" * 60)
    
    # 连接服务器
    print(f"\n📡 连接服务器 {SERVER_IP}...")
    ssh = None
    try:
        ssh = connect_ssh(SSH_CONFIG)
        print("✅ 连接成功！\n")
        
        # 上传修复后的 requirements.txt
        print("=" * 60)
        print("步骤 1/4: 上传修复后的 requirements.txt")
        print("=" * 60)
        
        sftp = ssh.open_sftp()
        local_file = "backend/requirements.txt"
        remote_file = f"{PROJECT_DIR}/backend/requirements.txt"
        
        print(f"📤 上传: {local_file} -> {remote_file}")
        sftp.put(local_file, remote_file)
        sftp.close()
        print("✅ 上传完成！\n")
        
        # 停止容器
        print("=" * 60)
        print("步骤 2/4: 停止容器")
        print("=" * 60)
        execute_command(ssh, f"cd {PROJECT_DIR} && docker-compose down")
        print()
        
        # 只删除 backend 镜像（保留缓存层）
        print("=" * 60)
        print("步骤 3/4: 清理 backend 镜像")
        print("=" * 60)
        execute_command(ssh, "docker rmi weld-system-backend 2>/dev/null || true", show_output=False)
        print("✅ 清理完成\n")
        
        # 使用缓存构建（不加 --no-cache）
        print("=" * 60)
        print("步骤 4/4: 构建并启动服务 (使用缓存)")
        print("=" * 60)
        print("🔨 开始构建...")
        print("💡 提示: 使用缓存构建，速度会快很多！\n")
        
        # 执行构建
        channel = ssh.get_transport().open_session()
        channel.get_pty()
        channel.exec_command(f"cd {PROJECT_DIR} && docker-compose build backend && docker-compose up -d")
        
        # 实时显示输出
        while True:
            if channel.recv_ready():
                output = channel.recv(1024).decode('utf-8', errors='ignore')
                print(output, end='', flush=True)
            
            if channel.exit_status_ready():
                # 读取剩余输出
                while channel.recv_ready():
                    output = channel.recv(1024).decode('utf-8', errors='ignore')
                    print(output, end='', flush=True)
                break
            
            time.sleep(0.1)
        
        exit_code = channel.recv_exit_status()
        channel.close()
        
        if exit_code == 0:
            print("\n" + "=" * 60)
            print("✅ 构建成功！")
            print("=" * 60)
            
            # 检查服务状态
            print("\n📊 服务状态:")
            execute_command(ssh, f"cd {PROJECT_DIR} && docker-compose ps")
            
            print("\n" + "=" * 60)
            print("🎉 部署完成！")
            print("=" * 60)
            print(f"\n访问地址: http://{SERVER_IP}")
            print(f"API 文档: http://{SERVER_IP}/api/docs")
        else:
            print("\n" + "=" * 60)
            print("❌ 构建失败！")
            print("=" * 60)
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if ssh is not None:
            ssh.close()

if __name__ == "__main__":
    quick_rebuild()

