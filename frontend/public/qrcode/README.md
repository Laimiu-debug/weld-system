# 收款码上传说明

请将收款码图片放在此目录（仅 `PAYMENT_PROVIDER=manual` 时使用）：

| 文件 | 说明 |
|------|------|
| `alipay.JPG` | 支付宝收款码 |
| `wechat.JPG` | 微信收款码 |

当前生产模式：`PAYMENT_PROVIDER=xunhu`（虎皮椒自动到账）。

- 回调地址：`https://api.sdhaohan.cn/api/v1/payments/callback/xunhu`
- 配置项：`XUNHU_APPID` / `XUNHU_APPSECRET` / `XUNHU_API_URL` / `PAYMENT_NOTIFY_URL` / `PAYMENT_RETURN_URL`
- 一个虎皮椒 APPID 通常对应一个渠道（微信或支付宝）；两种都要时需在后台分别开通渠道
