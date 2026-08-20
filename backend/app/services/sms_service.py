"""
SMS service for sending verification codes.
Supports multiple SMS providers: Aliyun SMS, Tencent Cloud SMS, Yunpian SMS.
"""
import json
import logging
import hashlib
import time
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for sending SMS via different providers."""

    def __init__(self):
        """Initialize SMS service."""
        self.provider = getattr(settings, 'SMS_PROVIDER', 'aliyun')
        logger.info(f"SMS service initialized with provider: {self.provider}")

    def send_verification_code(
        self,
        phone: str,
        code: str,
        purpose: str = "login",
        expires_minutes: int = 10
    ) -> bool:
        """
        Send verification code SMS.
        
        Args:
            phone: Phone number (Chinese format: 1xxxxxxxxxx)
            code: Verification code
            purpose: Purpose of verification (login, register, reset_password)
            expires_minutes: Code expiration time in minutes
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Validate phone number format
        if not self._validate_phone(phone):
            logger.error(f"Invalid phone number format: {phone}")
            return False

        purpose_text = {
            "login": "登录",
            "register": "注册",
            "reset_password": "重置密码",
            "bind_phone": "绑定手机",
        }.get(purpose, "验证")

        template_params = {
            "code": code,
            "minutes": str(expires_minutes)
        }

        sent = self.send_sms(
            phone=phone,
            template_code=self._get_template_code(purpose),
            template_params=template_params
        )
        if not sent and settings.DEVELOPMENT:
            logger.warning(
                "[DEVELOPMENT] SMS mock ok: phone=%s purpose=%s code=%s",
                phone,
                purpose,
                code,
            )
            return True
        return sent

    def send_sms(
        self,
        phone: str,
        template_code: str,
        template_params: Dict[str, str],
        sign_name: Optional[str] = None
    ) -> bool:
        """
        Send SMS using configured provider.
        
        Args:
            phone: Phone number
            template_code: SMS template code
            template_params: Template parameters
            sign_name: SMS signature name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if self.provider == 'aliyun':
                return self._send_via_aliyun(phone, template_code, template_params, sign_name)
            elif self.provider == 'tencent':
                return self._send_via_tencent(phone, template_code, template_params, sign_name)
            elif self.provider == 'yunpian':
                return self._send_via_yunpian(phone, template_code, template_params)
            else:
                logger.error(f"Unknown SMS provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}", exc_info=True)
            return False

    def _send_via_aliyun(
        self,
        phone: str,
        template_code: str,
        template_params: Dict[str, str],
        sign_name: Optional[str] = None
    ) -> bool:
        """Send SMS via Aliyun SMS API."""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest
            
            sign_name = sign_name or settings.ALIYUN_SMS_SIGN_NAME
            
            client = AcsClient(
                settings.ALIYUN_ACCESS_KEY_ID,
                settings.ALIYUN_ACCESS_KEY_SECRET,
                settings.ALIYUN_REGION_ID or 'cn-hangzhou'
            )
            
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            request.add_query_param('PhoneNumbers', phone)
            request.add_query_param('SignName', sign_name)
            request.add_query_param('TemplateCode', template_code)
            request.add_query_param('TemplateParam', json.dumps(template_params))
            
            response = client.do_action_with_exception(request)
            response_data = json.loads(response)
            
            if response_data.get('Code') == 'OK':
                logger.info(f"SMS sent successfully to {phone} via Aliyun")
                return True
            else:
                logger.error(f"Aliyun SMS failed: {response_data.get('Message')}")
                return False
                
        except ImportError:
            logger.error("Aliyun SDK not installed. Run: pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi")
            return False
        except Exception as e:
            logger.error(f"Aliyun SMS send failed: {str(e)}", exc_info=True)
            return False

    def _send_via_tencent(
        self,
        phone: str,
        template_code: str,
        template_params: Dict[str, str],
        sign_name: Optional[str] = None
    ) -> bool:
        """Send SMS via Tencent Cloud SMS API."""
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.sms.v20210111 import sms_client, models
            
            sign_name = sign_name or settings.TENCENT_SMS_SIGN_NAME
            
            # Initialize credential
            cred = credential.Credential(
                settings.TENCENT_SECRET_ID,
                settings.TENCENT_SECRET_KEY
            )
            
            # Initialize HTTP profile
            httpProfile = HttpProfile()
            httpProfile.endpoint = "sms.tencentcloudapi.com"
            
            # Initialize client profile
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            # Initialize SMS client
            client = sms_client.SmsClient(cred, settings.TENCENT_SMS_REGION or "ap-guangzhou", clientProfile)
            
            # Build request
            req = models.SendSmsRequest()
            req.SmsSdkAppId = settings.TENCENT_SMS_APP_ID
            req.SignName = sign_name
            req.TemplateId = template_code
            req.TemplateParamSet = [template_params.get('code', ''), template_params.get('minutes', '10')]
            req.PhoneNumberSet = [f"+86{phone}"]
            
            # Send SMS
            resp = client.SendSms(req)
            
            if resp.SendStatusSet[0].Code == "Ok":
                logger.info(f"SMS sent successfully to {phone} via Tencent Cloud")
                return True
            else:
                logger.error(f"Tencent SMS failed: {resp.SendStatusSet[0].Message}")
                return False
                
        except ImportError:
            logger.error("Tencent Cloud SDK not installed. Run: pip install tencentcloud-sdk-python")
            return False
        except Exception as e:
            logger.error(f"Tencent SMS send failed: {str(e)}", exc_info=True)
            return False

    def _send_via_yunpian(
        self,
        phone: str,
        template_code: str,
        template_params: Dict[str, str]
    ) -> bool:
        """Send SMS via Yunpian SMS API."""
        try:
            import requests
            
            url = "https://sms.yunpian.com/v2/sms/tpl_single_send.json"
            
            # Build template content
            tpl_value = "&".join([f"#{key}#={value}" for key, value in template_params.items()])
            
            data = {
                "apikey": settings.YUNPIAN_API_KEY,
                "mobile": phone,
                "tpl_id": template_code,
                "tpl_value": tpl_value
            }
            
            response = requests.post(url, data=data)
            result = response.json()
            
            if result.get('code') == 0:
                logger.info(f"SMS sent successfully to {phone} via Yunpian")
                return True
            else:
                logger.error(f"Yunpian SMS failed: {result.get('msg')}")
                return False
                
        except ImportError:
            logger.error("Requests library not installed. Run: pip install requests")
            return False
        except Exception as e:
            logger.error(f"Yunpian SMS send failed: {str(e)}", exc_info=True)
            return False

    def _validate_phone(self, phone: str) -> bool:
        """Validate Chinese phone number format."""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))

    def _get_template_code(self, purpose: str) -> str:
        """Get SMS template code based on purpose."""
        template_mapping = {
            "login": getattr(settings, 'SMS_TEMPLATE_LOGIN', 'SMS_LOGIN'),
            "register": getattr(settings, 'SMS_TEMPLATE_REGISTER', 'SMS_REGISTER'),
            "reset_password": getattr(settings, 'SMS_TEMPLATE_RESET_PASSWORD', 'SMS_RESET_PASSWORD'),
            "bind_phone": getattr(settings, 'SMS_TEMPLATE_BIND_PHONE', None)
                or getattr(settings, 'SMS_TEMPLATE_LOGIN', 'SMS_LOGIN'),
        }
        return template_mapping.get(purpose, 'SMS_LOGIN')


# Create global instance
sms_service = SMSService()

