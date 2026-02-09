#!/usr/bin/env python3
"""
配置 Docker 镜像加速器
"""
import paramiko
import sys

SERVER_IP = "43.142.188.252"
SSH_KEY = "server-key.pem"
SSH_USER = "root"
SSH_PASSWORD = "Weld2024"

def setup_docker_mirror():
    """配置 Docker 镜像加速"""
    print("=" * 60)
    print("🚀 配置 Docker 镜像加速器")
    print("=" * 60)

    # 连接服务器
    print(f"\n📡 连接服务器 {SERVER_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=SERVER_IP,
            username=SSH_USER,
            password=SSH_PASSWORD,
            key_filename=SSH_KEY,
            timeout=30
        )
        print("✅ 连接成功！\n")
        
        # Docker daemon 配置
        daemon_config = '''{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}'''
        
        print("📝 配置 Docker daemon.json...")
        commands = [
            # 创建 Docker 配置目录
            "mkdir -p /etc/docker",
            
            # 备份现有配置
            "if [ -f /etc/docker/daemon.json ]; then cp /etc/docker/daemon.json /etc/docker/daemon.json.bak; fi",
            
            # 写入新配置
            f"cat > /etc/docker/daemon.json << 'EOF'\n{daemon_config}\nEOF",
            
            # 重启 Docker
            "systemctl daemon-reload",
            "systemctl restart docker",
            
            # 验证配置
            "docker info | grep -A 5 'Registry Mirrors'"
        ]
        
        for cmd in commands:
            print(f"执行: {cmd[:50]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code != 0:
                error = stderr.read().decode('utf-8')
                if error and 'grep' not in cmd:  # grep 没找到不算错误
                    print(f"⚠️  警告: {error}")
            else:
                output = stdout.read().decode('utf-8')
                if output and 'Registry Mirrors' in cmd:
                    print(f"✅ 镜像加速器配置成功:\n{output}")
        
        print("\n" + "=" * 60)
        print("✅ Docker 镜像加速器配置完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    setup_docker_mirror()

