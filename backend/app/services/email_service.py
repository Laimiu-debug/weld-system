"""
Email service for sending verification codes and notifications.
Supports multiple email providers: SMTP, SendGrid, Aliyun DirectMail.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails via different providers."""

    def __init__(self):
        """Initialize email service."""
        self.provider = getattr(settings, 'EMAIL_PROVIDER', 'smtp')
        logger.info(f"Email service initialized with provider: {self.provider}")

    def send_verification_code(
        self,
        to_email: str,
        code: str,
        purpose: str = "login",
        expires_minutes: int = 10
    ) -> bool:
        """
        Send verification code email.
        
        Args:
            to_email: Recipient email address
            code: Verification code
            purpose: Purpose of verification (login, register, reset_password)
            expires_minutes: Code expiration time in minutes
            
        Returns:
            True if sent successfully, False otherwise
        """
        purpose_text = {
            "login": "登录",
            "register": "注册",
            "reset_password": "重置密码"
        }.get(purpose, "验证")

        subject = f"【焊序】{purpose_text}验证码"
        
        html_content = self._generate_verification_email_html(
            code=code,
            purpose=purpose_text,
            expires_minutes=expires_minutes
        )
        
        text_content = f"""
        【焊序】{purpose_text}验证码
        
        您的验证码是: {code}
        
        验证码有效期为 {expires_minutes} 分钟，请尽快使用。
        如果这不是您的操作，请忽略此邮件。
        
        此邮件由系统自动发送，请勿回复。
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    def send_invitation_email(
        self,
        to_email: str,
        company_name: str,
        invite_url: str,
        invitation_code: str,
        message: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        subject = f"【焊序】邀请你加入{company_name}"
        note = message or "管理员邀请你加入企业工作区。"
        expires_text = expires_at.strftime("%Y-%m-%d %H:%M") if expires_at else "7天内"
        html_content = f"""
        <p>你收到来自 <strong>{company_name}</strong> 的焊序企业邀请。</p>
        <p>{note}</p>
        <p>邀请码：<strong>{invitation_code}</strong></p>
        <p>请在 {expires_text} 前点击下方链接完成注册并加入企业：</p>
        <p><a href="{invite_url}">{invite_url}</a></p>
        <p>如果这不是你的操作，请忽略此邮件。</p>
        """
        text_content = (
            f"【焊序】邀请你加入{company_name}\n\n"
            f"{note}\n邀请码：{invitation_code}\n"
            f"注册链接：{invite_url}\n有效期至：{expires_text}\n"
        )
        try:
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )
        except Exception:
            logger.exception("Failed to send invitation email to %s", to_email)
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send email using configured provider.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (fallback)
            from_email: Sender email (optional)
            from_name: Sender name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if self.provider == 'smtp':
                return self._send_via_smtp(
                    to_email, subject, html_content, text_content, from_email, from_name
                )
            elif self.provider == 'sendgrid':
                return self._send_via_sendgrid(
                    to_email, subject, html_content, text_content, from_email, from_name
                )
            elif self.provider == 'aliyun':
                return self._send_via_aliyun(
                    to_email, subject, html_content, text_content, from_email, from_name
                )
            else:
                logger.error(f"Unknown email provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            return False

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email via SMTP."""
        try:
            from_email = from_email or settings.EMAILS_FROM_EMAIL
            from_name = from_name or settings.EMAILS_FROM_NAME
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}", exc_info=True)
            return False

    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email via SendGrid API."""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            from_email = from_email or settings.EMAILS_FROM_EMAIL
            from_name = from_name or settings.EMAILS_FROM_NAME
            
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            
            mail = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                mail.add_content(Content("text/plain", text_content))
            
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid returned status code: {response.status_code}")
                return False
                
        except ImportError:
            logger.error("SendGrid library not installed. Run: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"SendGrid send failed: {str(e)}", exc_info=True)
            return False

    def _send_via_aliyun(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email via Aliyun DirectMail API."""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest
            
            from_email = from_email or settings.EMAILS_FROM_EMAIL
            from_name = from_name or settings.EMAILS_FROM_NAME
            
            client = AcsClient(
                settings.ALIYUN_ACCESS_KEY_ID,
                settings.ALIYUN_ACCESS_KEY_SECRET,
                settings.ALIYUN_REGION_ID or 'cn-hangzhou'
            )
            
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dm.aliyuncs.com')
            request.set_method('POST')
            request.set_version('2015-11-23')
            request.set_action_name('SingleSendMail')
            
            request.add_query_param('AccountName', from_email)
            request.add_query_param('FromAlias', from_name)
            request.add_query_param('AddressType', '1')
            request.add_query_param('ToAddress', to_email)
            request.add_query_param('Subject', subject)
            request.add_query_param('HtmlBody', html_content)
            
            if text_content:
                request.add_query_param('TextBody', text_content)
            
            response = client.do_action_with_exception(request)
            
            logger.info(f"Email sent successfully to {to_email} via Aliyun DirectMail")
            return True
            
        except ImportError:
            logger.error("Aliyun SDK not installed. Run: pip install aliyun-python-sdk-core aliyun-python-sdk-dm")
            return False
        except Exception as e:
            logger.error(f"Aliyun DirectMail send failed: {str(e)}", exc_info=True)
            return False

    def _generate_verification_email_html(
        self,
        code: str,
        purpose: str,
        expires_minutes: int
    ) -> str:
        """Generate HTML content for verification email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>验证码</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">焊序</h1>
                                    <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">Hanxu</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 20px;">您的{purpose}验证码</h2>
                                    <p style="color: #666666; line-height: 1.6; margin: 0 0 30px 0;">
                                        您正在进行{purpose}操作，请使用以下验证码完成验证：
                                    </p>
                                    
                                    <!-- Verification Code -->
                                    <div style="background-color: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 0 0 30px 0;">
                                        <div style="font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                            {code}
                                        </div>
                                    </div>
                                    
                                    <p style="color: #666666; line-height: 1.6; margin: 0 0 10px 0;">
                                        <strong>重要提示：</strong>
                                    </p>
                                    <ul style="color: #666666; line-height: 1.8; margin: 0 0 20px 0; padding-left: 20px;">
                                        <li>验证码有效期为 <strong>{expires_minutes} 分钟</strong>，请尽快使用</li>
                                        <li>请勿将验证码告知他人</li>
                                        <li>如果这不是您的操作，请忽略此邮件</li>
                                    </ul>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 20px 30px; border-top: 1px solid #e9ecef;">
                                    <p style="color: #999999; font-size: 12px; line-height: 1.6; margin: 0; text-align: center;">
                                        此邮件由系统自动发送，请勿回复<br>
                                        © {datetime.now().year} 焊序 版权所有
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """


# Create global instance
email_service = EmailService()

