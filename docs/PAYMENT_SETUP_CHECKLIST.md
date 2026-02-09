# 支付功能集成检查清单

## 📋 准备阶段

### 1. 选择支付服务商
- [ ] 注册聚合支付平台账号（推荐：Ping++、BeeCloud）
- [ ] 完成企业认证（需要营业执照）
- [ ] 申请开通支付渠道（支付宝、微信支付）
- [ ] 获取API密钥和配置信息

**所需材料：**
- 营业执照
- 法人身份证
- 对公账户信息
- 网站备案信息（如有）

---

## 🔧 后端配置

### 2. 安装依赖

```bash
cd backend

# 如果使用 Ping++
pip install pingpp

# 如果使用其他支付SDK，安装对应的包
# pip install alipay-sdk-python
# pip install wechatpy
```

### 3. 环境变量配置

在 `backend/.env` 文件中添加：

```env
# ==================== 支付配置 ====================

# 支付服务商 (pingpp, mock)
PAYMENT_PROVIDER=pingpp

# Ping++ 配置
PAYMENT_APP_ID=app_xxxxxxxxxx
PAYMENT_API_KEY=sk_live_xxxxxxxxxx
PAYMENT_APP_SECRET=xxxxxxxxxx

# 支付回调地址（生产环境需要配置为真实域名）
PAYMENT_NOTIFY_URL=https://yourdomain.com/api/v1/payments/callback
PAYMENT_RETURN_URL=https://yourdomain.com/membership/payment-result

# Ping++ 公钥路径（用于验证回调签名）
PINGPP_PUBLIC_KEY_PATH=/path/to/pingpp_public_key.pem

# 支付渠道配置
PAYMENT_ALIPAY_ENABLED=true
PAYMENT_WECHAT_ENABLED=true
PAYMENT_BANK_ENABLED=false
```

### 4. 更新配置类

编辑 `backend/app/core/config.py`：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 支付配置
    PAYMENT_PROVIDER: str = "mock"  # pingpp, mock
    PAYMENT_APP_ID: Optional[str] = None
    PAYMENT_API_KEY: Optional[str] = None
    PAYMENT_APP_SECRET: Optional[str] = None
    PAYMENT_NOTIFY_URL: Optional[str] = None
    PAYMENT_RETURN_URL: Optional[str] = None
    PINGPP_PUBLIC_KEY_PATH: Optional[str] = None
    
    # 支付渠道开关
    PAYMENT_ALIPAY_ENABLED: bool = True
    PAYMENT_WECHAT_ENABLED: bool = True
    PAYMENT_BANK_ENABLED: bool = False
```

### 5. 数据库迁移

创建迁移文件添加支付网关相关字段：

```bash
cd backend

# 创建迁移
alembic revision -m "add_payment_gateway_fields"
```

编辑生成的迁移文件：

```python
def upgrade():
    # 添加支付网关字段到 subscription_transactions 表
    op.add_column('subscription_transactions',
        sa.Column('payment_gateway', sa.String(50), nullable=True)
    )
    op.add_column('subscription_transactions',
        sa.Column('gateway_transaction_id', sa.String(200), nullable=True)
    )
    op.add_column('subscription_transactions',
        sa.Column('gateway_response', sa.JSON(), nullable=True)
    )
    op.add_column('subscription_transactions',
        sa.Column('callback_received_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_column('subscription_transactions', 'callback_received_at')
    op.drop_column('subscription_transactions', 'gateway_response')
    op.drop_column('subscription_transactions', 'gateway_transaction_id')
    op.drop_column('subscription_transactions', 'payment_gateway')
```

执行迁移：

```bash
alembic upgrade head
```

### 6. 注册支付路由

编辑 `backend/app/api/v1/api.py`，确保支付路由已注册：

```python
from app.api.v1.endpoints import payments

# 添加支付路由
api_router.include_router(payments.router, prefix="/payments", tags=["支付"])
```

---

## 🎨 前端配置

### 7. 安装前端依赖

```bash
cd frontend

# 已有的依赖应该足够，如需要可以安装：
npm install qrcode.react
```

### 8. 添加路由

编辑 `frontend/src/App.tsx`，添加支付结果页面路由：

```typescript
import PaymentResult from '@/pages/Membership/PaymentResult'

// 在路由配置中添加
<Route path="/membership/payment-result" element={<PaymentResult />} />
```

### 9. 更新会员升级页面

编辑 `frontend/src/pages/Membership/MembershipUpgrade.tsx`，集成支付组件：

```typescript
import PaymentModal from '@/components/Payment/PaymentModal'

// 在组件中添加状态
const [paymentModalVisible, setPaymentModalVisible] = useState(false)
const [currentOrderId, setCurrentOrderId] = useState('')

// 修改支付处理函数
const handlePayment = async () => {
  // ... 创建订单逻辑 ...
  
  // 显示支付弹窗
  setCurrentOrderId(result.order_id)
  setPaymentModalVisible(true)
}

// 添加支付组件
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

---

## 🧪 测试阶段

### 10. 沙箱测试

#### Ping++ 沙箱测试

1. 登录 Ping++ 控制台
2. 切换到测试模式
3. 获取测试环境密钥
4. 更新 `.env` 文件使用测试密钥

```env
# 测试环境配置
PAYMENT_PROVIDER=pingpp
PAYMENT_APP_ID=app_test_xxxxxxxxxx
PAYMENT_API_KEY=sk_test_xxxxxxxxxx
```

#### 测试用例

- [ ] 支付宝扫码支付测试
- [ ] 微信扫码支付测试
- [ ] 支付成功回调测试
- [ ] 支付失败处理测试
- [ ] 支付超时测试
- [ ] 订单查询测试
- [ ] 退款功能测试

### 11. 本地测试

```bash
# 启动后端
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 启动前端
cd frontend
npm run dev
```

访问 `http://localhost:3000/membership/upgrade` 进行测试

### 12. 回调测试

由于本地环境无法接收支付网关回调，需要使用内网穿透工具：

**使用 ngrok：**

```bash
# 安装 ngrok
# 下载：https://ngrok.com/download

# 启动内网穿透
ngrok http 8000

# 获得公网地址，例如：https://xxxx.ngrok.io
# 更新 .env 中的回调地址
PAYMENT_NOTIFY_URL=https://xxxx.ngrok.io/api/v1/payments/callback
```

**使用 localtunnel：**

```bash
npm install -g localtunnel
lt --port 8000
```

---

## 🚀 生产部署

### 13. 生产环境配置

- [ ] 配置生产环境支付密钥（使用 live 密钥）
- [ ] 配置 HTTPS 证书
- [ ] 配置真实域名回调地址
- [ ] 在支付平台配置回调白名单

```env
# 生产环境配置
PAYMENT_PROVIDER=pingpp
PAYMENT_APP_ID=app_live_xxxxxxxxxx
PAYMENT_API_KEY=sk_live_xxxxxxxxxx
PAYMENT_NOTIFY_URL=https://api.yourdomain.com/api/v1/payments/callback
PAYMENT_RETURN_URL=https://www.yourdomain.com/membership/payment-result
```

### 14. 安全检查

- [ ] API密钥不要提交到代码仓库
- [ ] 使用环境变量管理敏感信息
- [ ] 启用HTTPS（生产环境必须）
- [ ] 验证所有支付回调签名
- [ ] 实现防重放攻击机制
- [ ] 记录所有支付操作日志
- [ ] 设置支付金额上下限
- [ ] 实现异常告警机制

### 15. 监控配置

- [ ] 配置支付成功率监控
- [ ] 配置支付异常告警
- [ ] 配置订单状态监控
- [ ] 配置日志收集（ELK/Sentry）

---

## 📊 验收标准

### 功能验收

- [ ] 用户可以选择支付方式
- [ ] 可以正确生成支付二维码
- [ ] 支付状态实时更新
- [ ] 支付成功后会员权益立即生效
- [ ] 支付失败有明确提示
- [ ] 可以查询订单状态
- [ ] 可以查看交易历史
- [ ] 退款功能正常

### 性能验收

- [ ] 支付订单创建时间 < 2秒
- [ ] 支付状态查询响应时间 < 1秒
- [ ] 支付回调处理时间 < 3秒
- [ ] 并发支付处理能力 > 100 TPS

### 安全验收

- [ ] 所有支付接口需要认证
- [ ] 回调签名验证通过
- [ ] 金额验证正确
- [ ] 防重放攻击有效
- [ ] 敏感信息加密存储

---

## 🆘 常见问题

### Q1: 支付回调收不到？

**解决方案：**
1. 检查回调地址是否配置正确
2. 确认服务器防火墙允许支付网关IP
3. 检查回调地址是否可以公网访问
4. 查看支付平台的回调日志

### Q2: 签名验证失败？

**解决方案：**
1. 确认使用的公钥是否正确
2. 检查签名算法是否匹配
3. 确认请求体没有被修改
4. 查看支付平台文档确认签名方式

### Q3: 支付成功但订单状态未更新？

**解决方案：**
1. 检查回调处理逻辑
2. 查看数据库事务是否提交
3. 检查日志是否有异常
4. 手动调用订单查询接口确认状态

### Q4: 测试环境无法收到回调？

**解决方案：**
1. 使用 ngrok 或 localtunnel 进行内网穿透
2. 或者使用支付平台提供的回调模拟工具
3. 或者直接调用回调接口进行测试

---

## 📞 技术支持

### Ping++ 支持
- 文档：https://www.pingxx.com/docs/
- 客服：support@pingxx.com
- 电话：400-xxx-xxxx

### 支付宝开放平台
- 文档：https://open.alipay.com/
- 论坛：https://openclub.alipay.com/

### 微信支付
- 文档：https://pay.weixin.qq.com/wiki/doc/api/
- 客服：https://kf.qq.com/

---

## ✅ 完成确认

完成以上所有步骤后，请确认：

- [ ] 所有配置项已正确填写
- [ ] 所有测试用例已通过
- [ ] 生产环境已正确部署
- [ ] 监控告警已配置
- [ ] 团队成员已培训
- [ ] 文档已更新

**签字确认：**

- 开发负责人：__________ 日期：__________
- 测试负责人：__________ 日期：__________
- 运维负责人：__________ 日期：__________
- 产品负责人：__________ 日期：__________

