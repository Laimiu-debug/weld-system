#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持续监控构建进度"""

import paramiko
import time

hostname = "43.142.188.252"
username = "root"
password = "Weld2024"
key_file = "server-key.pem"

print("🔍 开始监控构建进度...\n")

while True:
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, password=password, key_filename=key_file, timeout=10)
        
        # 检查构建进程
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'docker-compose build' | grep -v grep")
        build_process = stdout.read().decode('utf-8').strip()
        
        if not build_process:
            print("\n✅ 构建进程已完成！")
            
            # 检查容器状态
            print("\n" + "=" * 60)
            print("检查容器状态")
            print("=" * 60)
            stdin, stdout, stderr = ssh.exec_command("cd /home/ubuntu/weld-system && docker-compose ps")
            print(stdout.read().decode('utf-8'))
            
            # 检查镜像
            print("\n" + "=" * 60)
            print("检查Docker镜像")
            print("=" * 60)
            stdin, stdout, stderr = ssh.exec_command("docker images | grep weld-system")
            print(stdout.read().decode('utf-8'))
            
            ssh.close()
            break
        
        # 检查镜像状态
        stdin, stdout, stderr = ssh.exec_command("docker images | grep weld-system | wc -l")
        image_count = stdout.read().decode('utf-8').strip()
        
        print(f"⏳ 构建进行中... (已完成 {image_count}/3 个镜像)", end='\r')
        
        ssh.close()
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  监控已停止")
        break
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        time.sleep(5)

