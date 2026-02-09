# 支付功能快速开始指南

> 本指南帮助您在30分钟内完成支付功能的基础集成

## 🎯 目标

完成本指南后，您将能够：
- ✅ 在开发环境中测试支付流程
- ✅ 理解支付集成的核心概念
- ✅ 为生产环境部署做好准备

---

## 📦 方案选择

### 推荐方案：使用 Ping++（聚合支付）

**为什么选择 Ping++？**
- ✅ 一次对接，支持支付宝、微信等多种支付方式
- ✅ 开发简单，文档完善
- ✅ 有免费测试额度
- ✅ 支持沙箱测试

**费率：** 0.8% - 1.2%（比直连稍高，但开发成本低很多）

---

## 🚀 30分钟快速集成

### 第一步：注册 Ping++ 账号（5分钟）

1. 访问 https://www.pingxx.com/
2. 点击"免费注册"
3. 填写基本信息（邮箱、手机号）
4. 验证邮箱和手机号

**注意：** 测试环境不需要企业认证，可以直接使用

### 第二步：获取测试密钥（3分钟）

1. 登录 Ping++ 控制台
2. 进入"开发设置" → "API Keys"
3. 复制以下信息：
   - App ID: `app_test_xxxxxxxxxx`
   - API Key: `sk_test_xxxxxxxxxx`

### 第三步：配置后端（10分钟）

#### 1. 安装依赖

```bash
cd backend
pip install pingpp
```

#### 2. 配置环境变量

编辑 `backend/.env`：

```env
# 支付配置（测试环境）
PAYMENT_PROVIDER=pingpp
PAYMENT_APP_ID=app_test_xxxxxxxxxx
PAYMENT_API_KEY=sk_test_xxxxxxxxxx
PAYMENT_NOTIFY_URL=http://localhost:8000/api/v1/payments/callback
PAYMENT_RETURN_URL=http://localhost:3000/membership/payment-result
```

#### 3. 更新配置类

编辑 `backend/app/core/config.py`，添加：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 支付配置
    PAYMENT_PROVIDER: str = "mock"
    PAYMENT_APP_ID: Optional[str] = None
    PAYMENT_API_KEY: Optional[str] = None
    PAYMENT_NOTIFY_URL: Optional[str] = None
    PAYMENT_RETURN_URL: Optional[str] = None
```

#### 4. 文件已创建

以下文件已经为您创建好：
- ✅ `backend/app/services/payment_gateway.py` - 支付网关服务
- ✅ `backend/app/services/payment_service.py` - 已更新使用新网关

### 第四步：配置前端（7分钟）

#### 1. 文件已创建

以下文件已经为您创建好：
- ✅ `frontend/src/components/Payment/PaymentModal.tsx` - 支付弹窗组件
- ✅ `frontend/src/pages/Membership/PaymentResult.tsx` - 支付结果页面

#### 2. 添加路由

编辑 `frontend/src/App.tsx`，添加：

```typescript
import PaymentResult from '@/pages/Membership/PaymentResult'

// 在路由配置中添加
<Route path="/membership/payment-result" element={<PaymentResult />} />
```

#### 3. 集成到会员升级页面

编辑 `frontend/src/pages/Membership/MembershipUpgrade.tsx`：

```typescript
import PaymentModal from '@/components/Payment/PaymentModal'

// 在组件中添加状态
const [paymentModalVisible, setPaymentModalVisible] = useState(false)
const [currentOrderId, setCurrentOrderId] = useState('')

// 在支付处理函数中
const handlePayment = async () => {
  // ... 现有逻辑 ...
  
  if (result.success) {
    setCurrentOrderId(result.order_id)
    setPaymentModalVisible(true)
  }
}

// 在 JSX 中添加
<PaymentModal
  visible={paymentModalVisible}
  orderId={currentOrderId}
  amount={selectedAmount}
  planName={selectedPlanName}
  paymentMethod={paymentMethod}
  onSuccess={() => {
    setPaymentModalVisible(false)
    navigate('/membership/payment-result?status=success&order_id=' + currentOrderId)
  }}
  onCancel={() => setPaymentModalVisible(false)}
/>
```

### 第五步：测试（5分钟）

#### 1. 启动服务

```bash
# 终端1 - 启动后端
cd backend
python -m uvicorn app.main:app --reload

# 终端2 - 启动前端
cd frontend
npm run dev
```

#### 2. 测试流程

1. 访问 `http://localhost:3000/membership/upgrade`
2. 选择一个套餐
3. 选择支付方式（支付宝或微信）
4. 点击"确认支付"
5. 查看支付二维码弹窗
6. 使用 Ping++ 测试工具模拟支付成功

#### 3. Ping++ 测试工具

访问 Ping++ 控制台的"测试工具"：
- 可以模拟支付成功/失败
- 可以查看支付请求日志
- 可以手动触发回调

---

## 🧪 测试场景

### 场景1：支付成功

1. 创建支付订单
2. 显示二维码
3. 模拟支付成功
4. 收到回调
5. 订单状态更新
6. 会员权益激活

### 场景2：支付失败

1. 创建支付订单
2. 显示二维码
3. 模拟支付失败
4. 显示失败提示
5. 允许重新支付

### 场景3：支付超时

1. 创建支付订单
2. 显示二维码
3. 等待5分钟
4. 显示超时提示
5. 允许重新支付

---

## 📝 开发模式 vs 生产模式

### 开发模式（当前）

```env
PAYMENT_PROVIDER=mock  # 或 pingpp (测试环境)
PAYMENT_APP_ID=app_test_xxxxxxxxxx
PAYMENT_API_KEY=sk_test_xxxxxxxxxx
```

**特点：**
- 使用测试密钥
- 不需要真实支付
- 可以模拟各种场景
- 回调地址可以是 localhost

### 生产模式（上线后）

```env
PAYMENT_PROVIDER=pingpp
PAYMENT_APP_ID=app_live_xxxxxxxxxx
PAYMENT_API_KEY=sk_live_xxxxxxxxxx
PAYMENT_NOTIFY_URL=https://api.yourdomain.com/api/v1/payments/callback
PAYMENT_RETURN_URL=https://www.yourdomain.com/membership/payment-result
```

**要求：**
- 需要企业认证
- 使用生产密钥
- 真实支付
- 必须使用 HTTPS
- 回调地址必须是公网可访问

---

## 🔄 从开发到生产的迁移步骤

### 1. 完成企业认证（1-3个工作日）

在 Ping++ 控制台提交：
- 营业执照
- 法人身份证
- 对公账户信息

### 2. 申请支付渠道（3-7个工作日）

- 申请支付宝支付
- 申请微信支付
- 等待审核通过

### 3. 获取生产密钥

审核通过后，在控制台获取生产环境密钥

### 4. 更新配置

```bash
# 更新生产环境配置
vim backend/.env.production

# 重启服务
systemctl restart welding-backend
```

### 5. 测试验证

- 使用小额订单测试
- 验证支付流程
- 验证回调处理
- 验证退款功能

---

## 💡 常见问题

### Q: 本地测试时收不到回调怎么办？

**A:** 有三种方案：

1. **使用 ngrok（推荐）**
```bash
ngrok http 8000
# 获得公网地址：https://xxxx.ngrok.io
# 更新 PAYMENT_NOTIFY_URL=https://xxxx.ngrok.io/api/v1/payments/callback
```

2. **使用 Ping++ 回调模拟工具**
   - 在控制台手动触发回调
   - 适合调试回调处理逻辑

3. **直接调用回调接口**
```bash
curl -X POST http://localhost:8000/api/v1/payments/callback \
  -H "Content-Type: application/json" \
  -d '{"type":"charge.succeeded","data":{"object":{...}}}'
```

### Q: 如何切换支付方式？

**A:** 修改 `PAYMENT_PROVIDER` 环境变量：

```env
# 使用模拟支付（开发）
PAYMENT_PROVIDER=mock

# 使用 Ping++（测试/生产）
PAYMENT_PROVIDER=pingpp
```

### Q: 支付金额如何设置？

**A:** 在订阅计划中配置：

```sql
-- 查看订阅计划
SELECT * FROM subscription_plans;

-- 更新价格
UPDATE subscription_plans 
SET monthly_price = 99.00 
WHERE id = 'personal_pro';
```

---

## 📚 下一步

完成快速开始后，建议阅读：

1. **详细集成指南**
   - 📄 `docs/PAYMENT_INTEGRATION_GUIDE.md`
   - 完整的技术实现细节

2. **部署检查清单**
   - 📄 `docs/PAYMENT_SETUP_CHECKLIST.md`
   - 生产环境部署步骤

3. **API文档**
   - 访问 `http://localhost:8000/api/v1/docs`
   - 查看支付相关API

---

## 🎉 恭喜！

您已经完成了支付功能的基础集成！

**现在您可以：**
- ✅ 在开发环境测试支付流程
- ✅ 理解支付集成的核心概念
- ✅ 开始准备生产环境部署

**需要帮助？**
- 📧 技术支持：support@yourcompany.com
- 💬 开发者社区：https://community.yourcompany.com
- 📞 客服电话：400-xxx-xxxx

