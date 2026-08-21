"""
虎皮椒支付网关实现
适用于个人开发者，无需企业资质
官方文档：https://www.xunhupay.com/doc/api/pay.html
"""

from __future__ import annotations

import hashlib
import random
import string
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from app.core.config import settings
from app.services.payment_gateway import PaymentGatewayInterface


class XunhuPaymentGateway(PaymentGatewayInterface):
    """虎皮椒支付网关"""

    def __init__(self) -> None:
        self.appid = (settings.XUNHU_APPID or "").strip()
        self.appsecret = (settings.XUNHU_APPSECRET or "").strip()
        api_base = (getattr(settings, "XUNHU_API_URL", None) or "https://api.xunhupay.com").strip().rstrip("/")
        self.api_url = api_base
        self.pay_endpoint = f"{self.api_url}/payment/do.html"

        if not self.appid or not self.appsecret:
            raise ValueError("虎皮椒 XUNHU_APPID / XUNHU_APPSECRET 未配置")

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        官方算法：非空参数按键名 ASCII 排序，key=value&... 拼接后直接追加 APPSECRET，再 MD5（小写）。
        hash 自身与空值不参与签名。
        """
        items = []
        for key in sorted(params.keys()):
            if key == "hash":
                continue
            value = params[key]
            if value is None or value == "":
                continue
            items.append(f"{key}={value}")
        sign_str = "&".join(items) + self.appsecret
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    def _verify_sign(self, params: Dict[str, Any]) -> bool:
        if "hash" not in params:
            return False
        data = {k: v for k, v in params.items() if k != "hash"}
        received = str(params.get("hash") or "").lower()
        calculated = self._generate_sign(data).lower()
        return received == calculated and bool(received)

    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST JSON 创建支付订单，返回 url_qrcode（PC 展示图）与 url（移动端跳转）。
        """
        try:
            notify_url = (settings.PAYMENT_NOTIFY_URL or "").strip()
            return_url = (settings.PAYMENT_RETURN_URL or "").strip()
            if not notify_url:
                return {
                    "success": False,
                    "error": "PAYMENT_NOTIFY_URL 未配置",
                    "message": "支付回调地址未配置",
                }

            amount = float(payment_data["amount"])
            total_fee = f"{amount:.2f}"

            title = str(payment_data.get("subject") or "会员升级")[:120]
            # 去掉文档禁止的 % 与异常符号
            title = title.replace("%", "").replace("\n", " ").strip() or "会员升级"

            params: Dict[str, Any] = {
                "version": "1.1",
                "appid": self.appid,
                "trade_order_id": str(payment_data["order_id"]),
                "total_fee": total_fee,
                "title": title,
                "time": str(int(time.time())),
                "notify_url": notify_url,
                "nonce_str": self._generate_nonce_str(),
            }
            if return_url:
                # 回跳时带上订单号，便于前端结果页轮询
                sep = "&" if "?" in return_url else "?"
                params["return_url"] = f"{return_url}{sep}order_id={payment_data['order_id']}"
            if payment_data.get("body"):
                params["attach"] = str(payment_data.get("body"))[:200]
            params["plugins"] = "weldsystem"

            params["hash"] = self._generate_sign(params)

            response = requests.post(
                self.pay_endpoint,
                json=params,
                timeout=20,
                headers={"Content-Type": "application/json"},
            )
            result = response.json() if response.content else {}

            if int(result.get("errcode", -1)) != 0:
                return {
                    "success": False,
                    "error": result.get("errmsg") or f"errcode={result.get('errcode')}",
                    "message": f"创建支付订单失败: {result.get('errmsg') or result}",
                }

            url_qrcode = result.get("url_qrcode") or ""
            pay_url = result.get("url") or ""
            # PC 优先展示官方二维码图；无图时退回支付链接供前端再编码
            qr_code = url_qrcode or pay_url
            return {
                "success": True,
                "payment_url": pay_url or url_qrcode,
                "qr_code": qr_code,
                "qr_code_image": bool(url_qrcode),
                "charge_id": str(result.get("openid") or payment_data["order_id"]),
                "channel": payment_data.get("channel"),
                "message": "支付订单创建成功",
                "raw": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"创建支付订单失败: {str(e)}",
            }

    def query_payment(self, order_id: str) -> Dict[str, Any]:
        try:
            params = {
                "appid": self.appid,
                "out_trade_order": order_id,
                "time": str(int(time.time())),
                "nonce_str": self._generate_nonce_str(),
            }
            params["hash"] = self._generate_sign(params)
            response = requests.get(
                f"{self.api_url}/payment/query.html",
                params=params,
                timeout=10,
            )
            result = response.json() if response.content else {}
            if int(result.get("errcode", -1)) == 0:
                data = result.get("data") or result
                status = str(data.get("status", "OD"))
                # 回调文档：OD=已支付；查询侧部分环境返回 SUCCESS
                paid = status in {"OD", "SUCCESS", "WP"}
                return {
                    "success": True,
                    "status": "success" if paid else "pending",
                    "paid": paid,
                    "amount": float(data.get("total_fee", 0) or 0),
                    "transaction_id": data.get("transaction_id", ""),
                    "pay_time": data.get("time_end", ""),
                }
            return {
                "success": False,
                "status": "pending",
                "paid": False,
                "error": result.get("errmsg", "查询失败"),
            }
        except Exception as e:
            return {
                "success": False,
                "status": "pending",
                "paid": False,
                "error": str(e),
            }

    def verify_callback(self, data: Dict[str, Any], signature: str = "") -> bool:
        """兼容统一网关接口：验签用 data 内 hash，或显式 signature。"""
        try:
            payload = dict(data or {})
            if signature and "hash" not in payload:
                payload["hash"] = signature
            return self._verify_sign(payload)
        except Exception:
            return False

    def create_refund(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "MANUAL_REFUND_REQUIRED",
            "message": "虎皮椒需在后台手动退款，请登录虎皮椒商户后台处理",
        }

    def _generate_nonce_str(self) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=32))


def get_xunhu_gateway() -> XunhuPaymentGateway:
    return XunhuPaymentGateway()
