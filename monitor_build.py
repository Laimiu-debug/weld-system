#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持续监控构建进度"""

import time
from deployment_ssh import connect_ssh, load_ssh_config

config = load_ssh_config()

print("🔍 开始监控构建进度...\n")

while True:
    try:
        ssh = connect_ssh(config, timeout=10)
        
        # 检查构建进程
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'docker-compose build' | grep -v grep")
        build_process = stdout.read().decode('utf-8').strip()
        
        if not build_process:
            print("\n✅ 构建进程已完成！")
            
            # 检查容器状态
            print("\n" + "=" * 60)
            print("检查容器状态")
            print("=" * 60)
            stdin, stdout, stderr = ssh.exec_command(f"cd {config.project_dir} && docker-compose ps")
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

