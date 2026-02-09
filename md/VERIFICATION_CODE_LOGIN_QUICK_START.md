# 🚀 验证码登录功能 - 快速开始指南

## 📋 功能说明

系统现已支持**邮箱验证码登录**和**手机验证码登录**功能！

用户可以通过以下三种方式登录：
1. ✅ **密码登录**（传统方式）
2. ✅ **邮箱验证码登录**（新增）
3. ✅ **手机验证码登录**（新增）

---

## ⚡ 5分钟快速体验（开发环境）

### 步骤 1：启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 步骤 2：启动前端服务

```bash
cd frontend
npm run dev
```

### 步骤 3：测试验证码登录

1. 打开浏览器访问 `http://localhost:3000/login`
2. 点击"验证码登录" Tab
3. 输入任意邮箱（如：`test@example.com`）或手机号（如：`13800138000`）
4. 点击"发送验证码"
5. **查看后端控制台**，会显示：
   ```
   🔐 [开发环境] 验证码: 123456
   ```
6. 在前端输入验证码 `123456`
7. 点击"登录"

**注意**：开发环境下，验证码会在后端控制台打印，无需配置真实的邮件/短信服务。

---

## 🔧 生产环境配置

### 方案一：使用 Gmail 发送邮件验证码（最简单）

#### 1. 获取 Gmail 应用专用密码

1. 登录 Gmail
2. 访问 [Google 账号管理](https://myaccount.google.com/)
3. 点击"安全性" → "两步验证"（如未开启，先开启）
4. 点击"应用专用密码"
5. 选择"邮件"和"其他"，输入名称"焊接系统"
6. 复制生成的 16 位密码

#### 2. 配置环境变量

编辑 `backend/.env` 文件：

```bash
# 邮件服务配置
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 刚才复制的16位密码
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=焊接工艺管理系统

# 关闭开发模式
DEVELOPMENT=False
```

#### 3. 重启后端服务

```bash
cd backend
python -m uvicorn app.main:app --reload
```

#### 4. 测试

使用测试工具：
```bash
cd backend
python test_verification_code.py
```

选择"1. 测试邮件验证码发送"，输入你的邮箱，检查是否收到验证码邮件。

---

### 方案二：使用阿里云短信（推荐国内用户）

#### 1. 开通阿里云短信服务

1. 登录[阿里云控制台](https://www.aliyun.com/)
2. 搜索"短信服务"并开通
3. 完成实名认证

#### 2. 申请短信签名

1. 进入短信服务控制台
2. 点击"国内消息" → "签名管理" → "添加签名"
3. 填写签名名称：`焊接工艺管理系统`
4. 上传资质（企业营业执照或个人身份证）
5. 等待审核（通常 2 小时内）

#### 3. 申请短信模板

创建三个模板（登录、注册、重置密码）：

**登录验证码模板**：
```
您的登录验证码是：${code}，有效期${minutes}分钟，请勿泄露。
```

等待审核通过，记录模板 CODE（如：`SMS_123456789`）

#### 4. 创建 AccessKey

1. 进入 AccessKey 管理
2. 创建 AccessKey（建议使用 RAM 子账号）
3. 记录 AccessKeyId 和 AccessKeySecret

#### 5. 安装依赖

```bash
cd backend
pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi
```

或使用自动安装工具：
```bash
python install_email_sms_dependencies.py
```

#### 6. 配置环境变量

编辑 `backend/.env` 文件：

```bash
# 短信服务配置
SMS_PROVIDER=aliyun
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_REGION_ID=cn-hangzhou
ALIYUN_SMS_SIGN_NAME=焊接工艺管理系统
SMS_TEMPLATE_LOGIN=SMS_123456789        # 你的模板CODE
SMS_TEMPLATE_REGISTER=SMS_987654321
SMS_TEMPLATE_RESET_PASSWORD=SMS_456789123

# 关闭开发模式
DEVELOPMENT=False
```

#### 7. 测试

```bash
cd backend
python test_verification_code.py
```

选择"2. 测试短信验证码发送"，输入你的手机号，检查是否收到短信。

---

## 📁 文件说明

### 后端文件

| 文件 | 说明 |
|------|------|
| `app/services/email_service.py` | 邮件服务（支持SMTP、SendGrid、阿里云） |
| `app/services/sms_service.py` | 短信服务（支持阿里云、腾讯云、云片） |
| `app/api/v1/endpoints/auth.py` | 认证API（已集成验证码发送和登录） |
| `app/core/config.py` | 配置管理（新增邮件和短信配置项） |
| `.env.example` | 环境变量配置模板 |
| `EMAIL_SMS_SETUP_GUIDE.md` | 详细配置指南 |
| `test_verification_code.py` | 测试工具 |
| `install_email_sms_dependencies.py` | 依赖安装工具 |

### 前端文件

| 文件 | 说明 |
|------|------|
| `src/pages/Auth/Login.tsx` | 登录页面（新增验证码登录Tab） |
| `src/services/auth.ts` | 认证服务（新增验证码登录方法） |

---

## 🔍 API 接口

### 1. 发送验证码

**接口**: `POST /api/v1/auth/send-verification-code`

**请求**:
```json
{
  "account": "user@example.com",  // 邮箱或手机号
  "account_type": "email",         // "email" 或 "phone"
  "purpose": "login"               // "login", "register", "reset_password"
}
```

**响应**（开发环境）:
```json
{
  "message": "验证码已发送到您的邮箱（开发环境：123456）",
  "expires_in": 600,
  "code": "123456"  // 仅开发环境返回
}
```

**响应**（生产环境）:
```json
{
  "message": "验证码已发送到您的邮箱",
  "expires_in": 600
}
```

### 2. 验证码登录

**接口**: `POST /api/v1/auth/login-with-verification-code`

**请求**:
```json
{
  "account": "user@example.com",
  "verification_code": "123456",
  "account_type": "email"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user",
    ...
  }
}
```

---

## ❓ 常见问题

### Q1: 开发环境看不到验证码？

**A**: 查看后端控制台输出，验证码会打印在那里。

### Q2: Gmail SMTP 连接失败？

**A**: 
1. 确保已开启两步验证
2. 使用应用专用密码，不是 Gmail 登录密码
3. 检查防火墙是否阻止 587 端口

### Q3: 阿里云短信发送失败？

**A**:
1. 检查签名和模板是否审核通过
2. 确认 AccessKey 有短信发送权限
3. 检查短信余额是否充足
4. 验证手机号格式（1开头的11位数字）

### Q4: 生产环境邮件进入垃圾箱？

**A**:
1. 使用专业邮件服务（SendGrid）
2. 配置 SPF、DKIM 记录
3. 使用已验证的域名

---

## 📚 更多文档

- **详细配置指南**: `backend/EMAIL_SMS_SETUP_GUIDE.md`
- **实现报告**: `backend/VERIFICATION_CODE_LOGIN_IMPLEMENTATION.md`
- **环境变量配置**: `backend/.env.example`

---

## 🎉 完成！

现在你的系统已经支持验证码登录功能了！

**开发环境**：可以直接测试，验证码在控制台显示  
**生产环境**：配置邮件/短信服务后即可使用

祝使用愉快！🚀

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 `EMAIL_SMS_SETUP_GUIDE.md` 详细配置指南
2. 运行 `python test_verification_code.py` 测试服务
3. 检查后端日志获取详细错误信息

