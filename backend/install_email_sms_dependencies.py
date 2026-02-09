"""
安装邮件和短信服务依赖包

根据配置的服务提供商，安装相应的依赖包。
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command):
    """运行命令并打印输出"""
    print(f"\n🔧 执行: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 错误: {e.stderr}")
        return False


def install_dependencies():
    """安装依赖包"""
    print("=" * 60)
    print("📦 邮件和短信服务依赖安装工具")
    print("=" * 60)
    
    # 读取环境变量或使用默认值
    email_provider = os.getenv('EMAIL_PROVIDER', 'smtp')
    sms_provider = os.getenv('SMS_PROVIDER', 'aliyun')
    
    print(f"\n📧 邮件服务提供商: {email_provider}")
    print(f"📱 短信服务提供商: {sms_provider}")
    
    packages_to_install = []
    
    # 邮件服务依赖
    if email_provider == 'sendgrid':
        packages_to_install.append('sendgrid')
        print("\n✅ 将安装 SendGrid 依赖")
    elif email_provider == 'aliyun':
        packages_to_install.extend([
            'aliyun-python-sdk-core',
            'aliyun-python-sdk-dm'
        ])
        print("\n✅ 将安装阿里云邮件推送依赖")
    else:
        print("\n✅ SMTP 使用 Python 内置库，无需额外安装")
    
    # 短信服务依赖
    if sms_provider == 'aliyun':
        packages_to_install.extend([
            'aliyun-python-sdk-core',
            'aliyun-python-sdk-dysmsapi'
        ])
        print("✅ 将安装阿里云短信依赖")
    elif sms_provider == 'tencent':
        packages_to_install.append('tencentcloud-sdk-python')
        print("✅ 将安装腾讯云短信依赖")
    elif sms_provider == 'yunpian':
        packages_to_install.append('requests')
        print("✅ 将安装云片短信依赖（requests）")
    
    # 去重
    packages_to_install = list(set(packages_to_install))
    
    if not packages_to_install:
        print("\n✅ 无需安装额外依赖")
        return True
    
    print(f"\n📦 准备安装以下包:")
    for pkg in packages_to_install:
        print(f"   - {pkg}")
    
    # 确认安装
    response = input("\n是否继续安装? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ 安装已取消")
        return False
    
    # 安装依赖
    success = True
    for package in packages_to_install:
        if not run_command(f"{sys.executable} -m pip install {package}"):
            success = False
            print(f"❌ 安装 {package} 失败")
        else:
            print(f"✅ {package} 安装成功")
    
    return success


def check_installation():
    """检查依赖是否安装成功"""
    print("\n" + "=" * 60)
    print("🔍 检查依赖安装状态")
    print("=" * 60)
    
    email_provider = os.getenv('EMAIL_PROVIDER', 'smtp')
    sms_provider = os.getenv('SMS_PROVIDER', 'aliyun')
    
    all_ok = True
    
    # 检查邮件服务依赖
    if email_provider == 'sendgrid':
        try:
            import sendgrid
            print("✅ SendGrid 已安装")
        except ImportError:
            print("❌ SendGrid 未安装")
            all_ok = False
    elif email_provider == 'aliyun':
        try:
            from aliyunsdkcore.client import AcsClient
            print("✅ 阿里云邮件推送 SDK 已安装")
        except ImportError:
            print("❌ 阿里云邮件推送 SDK 未安装")
            all_ok = False
    
    # 检查短信服务依赖
    if sms_provider == 'aliyun':
        try:
            from aliyunsdkcore.client import AcsClient
            print("✅ 阿里云短信 SDK 已安装")
        except ImportError:
            print("❌ 阿里云短信 SDK 未安装")
            all_ok = False
    elif sms_provider == 'tencent':
        try:
            from tencentcloud.sms.v20210111 import sms_client
            print("✅ 腾讯云短信 SDK 已安装")
        except ImportError:
            print("❌ 腾讯云短信 SDK 未安装")
            all_ok = False
    elif sms_provider == 'yunpian':
        try:
            import requests
            print("✅ Requests 库已安装")
        except ImportError:
            print("❌ Requests 库未安装")
            all_ok = False
    
    return all_ok


def main():
    """主函数"""
    print("\n🚀 开始安装邮件和短信服务依赖...\n")
    
    # 检查是否在虚拟环境中
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  警告: 建议在虚拟环境中安装依赖")
        response = input("是否继续? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ 安装已取消")
            return
    
    # 安装依赖
    if install_dependencies():
        print("\n" + "=" * 60)
        print("✅ 依赖安装完成")
        print("=" * 60)
        
        # 检查安装状态
        if check_installation():
            print("\n✅ 所有依赖检查通过")
            print("\n📖 下一步:")
            print("   1. 配置 .env 文件中的邮件和短信服务参数")
            print("   2. 参考 EMAIL_SMS_SETUP_GUIDE.md 完成配置")
            print("   3. 重启后端服务")
        else:
            print("\n⚠️  部分依赖安装失败，请检查错误信息")
    else:
        print("\n❌ 依赖安装失败")
        sys.exit(1)


if __name__ == '__main__':
    main()

