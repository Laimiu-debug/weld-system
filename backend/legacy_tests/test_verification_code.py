"""
测试验证码发送功能

用于测试邮件和短信验证码发送是否正常工作。
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.email_service import email_service
from app.services.sms_service import sms_service


def test_email_verification():
    """测试邮件验证码发送"""
    print("\n" + "=" * 60)
    print("📧 测试邮件验证码发送")
    print("=" * 60)
    
    email = input("\n请输入测试邮箱地址: ").strip()
    if not email:
        print("❌ 邮箱地址不能为空")
        return False
    
    print(f"\n📤 正在发送验证码到 {email}...")
    print(f"📧 邮件服务提供商: {settings.EMAIL_PROVIDER}")
    
    # 生成测试验证码
    test_code = "123456"
    
    # 发送邮件
    success = email_service.send_verification_code(
        to_email=email,
        code=test_code,
        purpose="login",
        expires_minutes=10
    )
    
    if success:
        print(f"✅ 邮件发送成功！")
        print(f"🔐 验证码: {test_code}")
        print(f"⏰ 有效期: 10分钟")
        return True
    else:
        print(f"❌ 邮件发送失败")
        print(f"\n💡 提示:")
        print(f"   1. 检查 .env 文件中的邮件配置")
        print(f"   2. 如果使用 Gmail，确保已生成应用专用密码")
        print(f"   3. 检查网络连接")
        print(f"   4. 查看后端日志获取详细错误信息")
        return False


def test_sms_verification():
    """测试短信验证码发送"""
    print("\n" + "=" * 60)
    print("📱 测试短信验证码发送")
    print("=" * 60)
    
    phone = input("\n请输入测试手机号（格式：1xxxxxxxxxx）: ").strip()
    if not phone:
        print("❌ 手机号不能为空")
        return False
    
    # 验证手机号格式
    import re
    if not re.match(r'^1[3-9]\d{9}$', phone):
        print("❌ 手机号格式不正确，必须是1开头的11位数字")
        return False
    
    print(f"\n📤 正在发送验证码到 {phone}...")
    print(f"📱 短信服务提供商: {settings.SMS_PROVIDER}")
    
    # 生成测试验证码
    test_code = "123456"
    
    # 发送短信
    success = sms_service.send_verification_code(
        phone=phone,
        code=test_code,
        purpose="login",
        expires_minutes=10
    )
    
    if success:
        print(f"✅ 短信发送成功！")
        print(f"🔐 验证码: {test_code}")
        print(f"⏰ 有效期: 10分钟")
        print(f"\n💡 请检查手机是否收到短信")
        return True
    else:
        print(f"❌ 短信发送失败")
        print(f"\n💡 提示:")
        print(f"   1. 检查 .env 文件中的短信配置")
        print(f"   2. 确保短信签名和模板已审核通过")
        print(f"   3. 检查 AccessKey 权限")
        print(f"   4. 确认短信余额充足")
        print(f"   5. 查看后端日志获取详细错误信息")
        return False


def check_configuration():
    """检查配置"""
    print("\n" + "=" * 60)
    print("🔍 检查配置")
    print("=" * 60)
    
    print(f"\n📧 邮件服务配置:")
    print(f"   提供商: {settings.EMAIL_PROVIDER}")
    
    if settings.EMAIL_PROVIDER == 'smtp':
        print(f"   SMTP服务器: {settings.SMTP_SERVER}")
        print(f"   SMTP端口: {settings.SMTP_PORT}")
        print(f"   SMTP用户: {settings.SMTP_USER}")
        print(f"   发件人: {settings.EMAILS_FROM_EMAIL}")
        print(f"   发件人名称: {settings.EMAILS_FROM_NAME}")
    elif settings.EMAIL_PROVIDER == 'sendgrid':
        api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        print(f"   API Key: {'已配置' if api_key else '未配置'}")
    elif settings.EMAIL_PROVIDER == 'aliyun':
        access_key = getattr(settings, 'ALIYUN_ACCESS_KEY_ID', None)
        print(f"   AccessKey: {'已配置' if access_key else '未配置'}")
    
    print(f"\n📱 短信服务配置:")
    print(f"   提供商: {settings.SMS_PROVIDER}")
    
    if settings.SMS_PROVIDER == 'aliyun':
        access_key = getattr(settings, 'ALIYUN_ACCESS_KEY_ID', None)
        sign_name = getattr(settings, 'ALIYUN_SMS_SIGN_NAME', None)
        print(f"   AccessKey: {'已配置' if access_key else '未配置'}")
        print(f"   签名: {sign_name}")
        print(f"   登录模板: {getattr(settings, 'SMS_TEMPLATE_LOGIN', '未配置')}")
    elif settings.SMS_PROVIDER == 'tencent':
        secret_id = getattr(settings, 'TENCENT_SECRET_ID', None)
        print(f"   SecretId: {'已配置' if secret_id else '未配置'}")
    elif settings.SMS_PROVIDER == 'yunpian':
        api_key = getattr(settings, 'YUNPIAN_API_KEY', None)
        print(f"   API Key: {'已配置' if api_key else '未配置'}")
    
    print(f"\n🔧 环境:")
    print(f"   开发模式: {settings.DEVELOPMENT}")
    print(f"   调试模式: {settings.DEBUG}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🧪 验证码发送功能测试工具")
    print("=" * 60)
    
    # 检查配置
    check_configuration()
    
    while True:
        print("\n" + "=" * 60)
        print("请选择测试项目:")
        print("=" * 60)
        print("1. 测试邮件验证码发送")
        print("2. 测试短信验证码发送")
        print("3. 查看配置信息")
        print("0. 退出")
        print("=" * 60)
        
        choice = input("\n请输入选项 (0-3): ").strip()
        
        if choice == '1':
            test_email_verification()
        elif choice == '2':
            test_sms_verification()
        elif choice == '3':
            check_configuration()
        elif choice == '0':
            print("\n👋 再见！")
            break
        else:
            print("❌ 无效的选项，请重新选择")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 测试已中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

