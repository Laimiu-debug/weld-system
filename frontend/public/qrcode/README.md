# 收款码上传说明

请将收款码图片放在此目录：

| 文件 | 说明 |
|------|------|
| `alipay.JPG` | 支付宝收款码（前端读取此路径） |
| `wechat.JPG` | 微信收款码 |

当前模式：`PAYMENT_PROVIDER=manual`（虎皮椒审核通过前）

1. 用户升级会员 → 扫码按金额支付，备注填订单号  
2. 用户提交支付凭证（流水号/订单号）  
3. 管理员在 `/admin/pending-payments` 确认后开通会员  

虎皮椒签约成功后，把 `PAYMENT_PROVIDER` 改为 `xunhu` 并配置 APPID/SECRET 即可切自动到账。
