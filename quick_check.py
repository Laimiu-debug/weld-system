#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速检查服务器状态"""

import paramiko

hostname = "43.142.188.252"
username = "root"
password = "Weld2024"
key_file = "server-key.pem"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=hostname, username=username, password=password, key_filename=key_file, timeout=10)

print("=" * 60)
print("检查Docker容器状态")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command("cd /home/ubuntu/weld-system && docker-compose ps")
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

