#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速检查服务器状态"""

from deployment_ssh import connect_ssh, load_ssh_config

config = load_ssh_config()
ssh = connect_ssh(config, timeout=10)

print("=" * 60)
print("检查Docker容器状态")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command(f"cd {config.project_dir} && docker-compose ps")
print(stdout.read().decode('utf-8'))

print("\n" + "=" * 60)
print("检查Docker镜像")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command("docker images | grep -E 'weld-system|REPOSITORY'")
print(stdout.read().decode('utf-8'))

print("\n" + "=" * 60)
print("检查是否有构建进程")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'docker' | grep -v grep | head -5")
output = stdout.read().decode('utf-8')
if output:
    print(output)
else:
    print("没有Docker构建进程")

ssh.close()

