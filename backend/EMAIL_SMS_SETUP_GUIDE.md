# 📧📱 邮件和短信服务配置指南

本指南将帮助你配置邮件验证码和短信验证码功能。

---

## 📋 目录

1. [功能概述](#功能概述)
2. [邮件服务配置](#邮件服务配置)
3. [短信服务配置](#短信服务配置)
4. [开发环境测试](#开发环境测试)
5. [生产环境部署](#生产环境部署)
6. [常见问题](#常见问题)

---

## 🎯 功能概述

系统支持以下验证码登录方式：

- ✅ **邮箱验证码登录**：用户输入邮箱，接收验证码后登录
- ✅ **手机验证码登录**：用户输入手机号，接收短信验证码后登录
- ✅ **密码登录**：传统的账号密码登录方式

### 支持的服务提供商

**邮件服务：**
- SMTP（Gmail、QQ邮箱、163邮箱等）
- SendGrid（专业邮件服务）
- 阿里云邮件推送

**短信服务：**
- 阿里云短信
- 腾讯云短信
- 云片短信

---

## 📧 邮件服务配置

### 方案一：使用 Gmail SMTP（推荐用于开发测试）

#### 步骤 1：开启 Gmail 两步验证

1. 登录你的 Gmail 账号
2. 访问 [Google 账号管理](https://myaccount.google.com/)
3. 点击左侧"安全性"
4. 找到"登录 Google"部分
5. 点击"两步验证"并按提示开启

#### 步骤 2：生成应用专用密码

1. 在"安全性"页面，找到"应用专用密码"
2. 选择"邮件"和"其他（自定义名称）"
3. 输入名称，如"焊接系统"
4. 点击"生成"
5. 复制生成的 16 位密码（格式：xxxx xxxx xxxx xxxx）

#### 步骤 3：配置环境变量

在 `backend/.env` 文件中添加：

```bash
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 刚才生成的16位密码
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=焊接工艺管理系统
```

### 方案二：使用 QQ 邮箱 SMTP

#### 步骤 1：开启 SMTP 服务

1. 登录 QQ 邮箱
2. 点击"设置" -> "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 按提示发送短信验证
6. 获取授权码（16位）

#### 步骤 2：配置环境变量

```bash
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your-qq-number@qq.com
SMTP_PASSWORD=your-authorization-code  # QQ邮箱授权码
EMAILS_FROM_EMAIL=your-qq-number@qq.com
EMAILS_FROM_NAME=焊接工艺管理系统
```

### 方案三：使用 SendGrid（推荐用于生产环境）

#### 步骤 1：注册 SendGrid 账号

1. 访问 [SendGrid 官网](https://sendgrid.com/)
2. 注册免费账号（每天 100 封邮件）
3. 验证邮箱地址

#### 步骤 2：创建 API Key

1. 登录 SendGrid 控制台
2. 进入 Settings -> API Keys
3. 点击"Create API Key"
4. 选择"Full Access"
5. 复制生成的 API Key

#### 步骤 3：配置环境变量

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=焊接工艺管理系统
```

#### 步骤 4：验证发件人

在 SendGrid 控制台验证你的发件人邮箱地址。

### 方案四：使用阿里云邮件推送

#### 步骤 1：开通服务

1. 登录[阿里云控制台](https://www.aliyun.com/)
2. 搜索"邮件推送"并开通服务
3. 创建发信域名并完成验证

#### 步骤 2：创建 AccessKey

1. 进入 AccessKey 管理
2. 创建 AccessKey（建议使用 RAM 子账号）
3. 记录 AccessKeyId 和 AccessKeySecret

#### 步骤 3：配置环境变量

```bash
EMAIL_PROVIDER=aliyun
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_REGION_ID=cn-hangzhou
EMAILS_FROM_EMAIL=noreply@your-verified-domain.com
EMAILS_FROM_NAME=焊接工艺管理系统
```

---

## 📱 短信服务配置

### 方案一：使用阿里云短信（推荐）

#### 步骤 1：开通短信服务

1. 登录[阿里云控制台](https://www.aliyun.com/)
2. 搜索"短信服务"并开通
3. 完成实名认证

#### 步骤 2：申请短信签名

1. 进入短信服务控制台
2. 点击"国内消息" -> "签名管理" -> "添加签名"
3. 填写签名信息（如：焊接工艺管理系统）
4. 上传相关资质（企业营业执照或个人身份证）
5. 等待审核（通常 2 小时内）

#### 步骤 3：申请短信模板

创建三个模板：

**登录验证码模板：**
```
您的登录验证码是：${code}，有效期${minutes}分钟，请勿泄露。
```

**注册验证码模板：**
```
您的注册验证码是：${code}，有效期${minutes}分钟，请勿泄露。
```

**重置密码验证码模板：**
```
您的重置密码验证码是：${code}，有效期${minutes}分钟，请勿泄露。
```

等待模板审核通过，记录模板 CODE（如：SMS_123456789）

#### 步骤 4：创建 AccessKey

1. 进入 AccessKey 管理
2. 创建 AccessKey（建议使用 RAM 子账号并授予短信权限）
3. 记录 AccessKeyId 和 AccessKeySecret

#### 步骤 5：配置环境变量

```bash
SMS_PROVIDER=aliyun
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_REGION_ID=cn-hangzhou
ALIYUN_SMS_SIGN_NAME=焊接工艺管理系统
SMS_TEMPLATE_LOGIN=SMS_123456789
SMS_TEMPLATE_REGISTER=SMS_987654321
SMS_TEMPLATE_RESET_PASSWORD=SMS_456789123
```

#### 步骤 6：安装依赖

```bash
cd backend
pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi
```

### 方案二：使用腾讯云短信

#### 步骤 1：开通服务

1. 登录[腾讯云控制台](https://cloud.tencent.com/)
2. 搜索"短信"并开通服务
3. 完成实名认证

#### 步骤 2：申请签名和模板

流程与阿里云类似，申请签名和三个验证码模板。

#### 步骤 3：配置环境变量

```bash
SMS_PROVIDER=tencent
TENCENT_SECRET_ID=your-secret-id
TENCENT_SECRET_KEY=your-secret-key
TENCENT_SMS_APP_ID=your-app-id
TENCENT_SMS_SIGN_NAME=焊接工艺管理系统
TENCENT_SMS_REGION=ap-guangzhou
```

#### 步骤 4：安装依赖

```bash
pip install tencentcloud-sdk-python
```

### 方案三：使用云片短信（适合快速测试）

#### 步骤 1：注册账号

1. 访问[云片官网](https://www.yunpian.com/)
2. 注册账号（注册即送测试短信）

#### 步骤 2：获取 API Key

1. 登录控制台
2. 进入"账户设置" -> "API密钥"
3. 复制 API Key

#### 步骤 3：配置环境变量

```bash
SMS_PROVIDER=yunpian
YUNPIAN_API_KEY=your-api-key
```

#### 步骤 4：安装依赖

```bash
pip install requests
```

---

## 🧪 开发环境测试

### 开发模式特性

在开发环境（`DEVELOPMENT=True`）下：

1. **验证码会在控制台打印**，无需真实发送
2. **API 响应会包含验证码**（仅开发环境）
3. 即使邮件/短信发送失败，也会返回成功

### 测试步骤

1. 确保 `.env` 文件中设置：
```bash
DEVELOPMENT=True
```

2. 启动后端服务：
```bash
cd backend
python -m uvicorn app.main:app --reload
```

3. 测试发送验证码：
```bash
curl -X POST http://localhost:8000/api/v1/auth/send-verification-code \
  -H "Content-Type: application/json" \
  -d '{
    "account": "test@example.com",
    "account_type": "email",
    "purpose": "login"
  }'
```

4. 查看控制台输出，会显示：
```
🔐 [开发环境] 验证码: 123456
```

5. 使用验证码登录：
```bash
curl -X POST http://localhost:8000/api/v1/auth/login-with-verification-code \
  -H "Content-Type: application/json" \
  -d '{
    "account": "test@example.com",
    "verification_code": "123456",
    "account_type": "email"
  }'
```

---

## 🚀 生产环境部署

### 部署前检查清单

- [ ] 已配置真实的邮件服务（SMTP/SendGrid/阿里云）
- [ ] 已配置真实的短信服务（阿里云/腾讯云/云片）
- [ ] 短信签名和模板已审核通过
- [ ] AccessKey 使用 RAM 子账号（最小权限原则）
- [ ] 设置 `DEVELOPMENT=False`
- [ ] 测试邮件和短信发送功能

### 安全建议

1. **使用 RAM 子账号**：不要使用主账号的 AccessKey
2. **最小权限原则**：只授予必要的权限（短信发送、邮件发送）
3. **定期更换密钥**：建议每 3-6 个月更换一次
4. **监控使用量**：设置短信和邮件的使用量告警
5. **防止滥用**：
   - 实现 IP 限流
   - 添加图形验证码
   - 限制单个账号的发送频率

---

## ❓ 常见问题

### Q1: Gmail SMTP 连接失败

**A:** 检查以下几点：
1. 是否开启了两步验证
2. 是否使用了应用专用密码（不是 Gmail 登录密码）
3. 是否允许"不够安全的应用"访问（旧版 Gmail）
4. 防火墙是否阻止了 587 端口

### Q2: 阿里云短信发送失败

**A:** 常见原因：
1. 签名或模板未审核通过
2. AccessKey 权限不足
3. 短信余额不足
4. 模板变量不匹配（检查 `${code}` 和 `${minutes}`）
5. 手机号格式错误（必须是 1 开头的 11 位数字）

### Q3: 开发环境看不到验证码

**A:** 检查：
1. `.env` 文件中 `DEVELOPMENT=True`
2. 查看后端控制台输出
3. 检查 API 响应中的 `code` 字段

### Q4: 生产环境邮件进入垃圾箱

**A:** 解决方案：
1. 使用专业邮件服务（SendGrid）
2. 配置 SPF、DKIM、DMARC 记录
3. 使用已验证的域名发送
4. 避免使用垃圾邮件关键词

### Q5: 短信发送成功但收不到

**A:** 检查：
1. 手机号是否正确
2. 是否被运营商拦截（检查垃圾短信）
3. 短信服务商控制台是否显示发送成功
4. 是否在黑名单中

---

## 📞 技术支持

如有问题，请查看：

- [阿里云短信文档](https://help.aliyun.com/product/44282.html)
- [腾讯云短信文档](https://cloud.tencent.com/document/product/382)
- [SendGrid 文档](https://docs.sendgrid.com/)

---

## 🎉 完成

配置完成后，你的系统将支持：

✅ 邮箱验证码登录  
✅ 手机验证码登录  
✅ 密码登录  
✅ 验证码找回密码  

祝你使用愉快！🚀

