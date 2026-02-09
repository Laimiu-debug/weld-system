# 支付功能集成指南

## 📋 目录
1. [当前状态分析](#当前状态分析)
2. [支付方案选择](#支付方案选择)
3. [集成步骤](#集成步骤)
4. [技术实现](#技术实现)
5. [测试方案](#测试方案)

---

## 🔍 当前状态分析

### 已有基础设施

#### 后端
- ✅ 数据模型：`Subscription`, `SubscriptionPlan`, `SubscriptionTransaction`
- ✅ 支付服务：`backend/app/services/payment_service.py`（模拟实现）
- ✅ 支付API：`backend/app/api/v1/endpoints/payments.py`
- ✅ 会员API：`backend/app/api/v1/endpoints/members.py`

#### 前端
- ✅ 会员升级页面：`frontend/src/pages/Membership/MembershipUpgrade.tsx`
- ✅ 支付方式选择：支付宝、微信、银行转账
- ✅ 会员服务：`frontend/src/services/membership.ts`

### 需要完善的部分
- ❌ 真实支付网关对接
- ❌ 支付回调处理
- ❌ 支付状态查询
- ❌ 订单管理
- ❌ 退款处理

---

## 💳 支付方案选择

### 方案对比

| 方案 | 优点 | 缺点 | 适用场景 | 费率 |
|------|------|------|----------|------|
| **支付宝 + 微信直连** | 费率低(0.6%) | 需要企业资质、开发复杂 | 大型企业 | 0.6% |
| **聚合支付（推荐）** | 接入简单、一次对接多种支付 | 费率稍高(0.8-1.2%) | 中小企业 | 0.8-1.2% |
| **Stripe** | 国际化、开发体验好 | 国内支持有限 | 海外业务 | 2.9%+¥2 |
| **PayPal** | 国际认可度高 | 国内使用少 | 海外业务 | 3.4%+固定费用 |

### 推荐方案：聚合支付

**推荐使用聚合支付平台**（如 Ping++、BeeCloud、易宝支付等）

#### 优势
1. **一次对接，支持多种支付方式**
   - 支付宝（扫码、H5、APP）
   - 微信支付（扫码、公众号、小程序）
   - 银联支付
   - Apple Pay

2. **开发成本低**
   - 统一API接口
   - 完善的SDK和文档
   - 沙箱测试环境

3. **功能完善**
   - 支付、退款、查询
   - 对账、分账
   - 风控系统

---

## 🚀 集成步骤

### 阶段一：准备工作（1-2天）

#### 1. 选择支付服务商
- [ ] 注册聚合支付平台账号（推荐：Ping++）
- [ ] 完成企业认证
- [ ] 获取API密钥（App ID、App Secret）
- [ ] 配置支付渠道（支付宝、微信）

#### 2. 环境配置
```bash
# 安装支付SDK
cd backend
pip install pingpp  # 或其他支付SDK
```

#### 3. 配置文件更新
在 `backend/.env` 添加：
```env
# 支付配置
PAYMENT_PROVIDER=pingpp  # 支付服务商
PAYMENT_APP_ID=your_app_id
PAYMENT_APP_SECRET=your_app_secret
PAYMENT_API_KEY=your_api_key
PAYMENT_WEBHOOK_SECRET=your_webhook_secret

# 支付回调地址
PAYMENT_NOTIFY_URL=https://yourdomain.com/api/v1/payments/callback
PAYMENT_RETURN_URL=https://yourdomain.com/membership/payment-result
```

### 阶段二：后端开发（3-5天）

#### 1. 更新支付服务
需要修改的文件：
- `backend/app/services/payment_service.py`
- `backend/app/api/v1/endpoints/payments.py`
- `backend/app/core/config.py`

#### 2. 实现功能
- [ ] 创建支付订单（调用支付网关）
- [ ] 生成支付二维码/链接
- [ ] 处理支付回调（异步通知）
- [ ] 查询支付状态
- [ ] 处理退款
- [ ] 订单管理

#### 3. 数据库迁移
可能需要添加新字段：
```sql
-- 添加支付网关相关字段
ALTER TABLE subscription_transactions 
ADD COLUMN payment_gateway VARCHAR(50),
ADD COLUMN gateway_transaction_id VARCHAR(200),
ADD COLUMN gateway_response JSONB,
ADD COLUMN callback_received_at TIMESTAMP;
```

### 阶段三：前端开发（2-3天）

#### 1. 支付流程优化
需要修改的文件：
- `frontend/src/pages/Membership/MembershipUpgrade.tsx`
- `frontend/src/services/membership.ts`

#### 2. 新增页面
- [ ] 支付结果页面（成功/失败）
- [ ] 支付二维码展示页面
- [ ] 订单详情页面

#### 3. 支付状态轮询
```typescript
// 轮询支付状态
const pollPaymentStatus = async (orderId: string) => {
  const maxAttempts = 60 // 最多轮询60次（5分钟）
  let attempts = 0
  
  const poll = setInterval(async () => {
    attempts++
    const status = await paymentService.getPaymentStatus(orderId)
    
    if (status.status === 'success') {
      clearInterval(poll)
      // 支付成功处理
    } else if (status.status === 'failed' || attempts >= maxAttempts) {
      clearInterval(poll)
      // 支付失败或超时处理
    }
  }, 5000) // 每5秒查询一次
}
```

### 阶段四：测试（2-3天）

#### 1. 沙箱测试
- [ ] 支付宝沙箱测试
- [ ] 微信支付沙箱测试
- [ ] 支付回调测试
- [ ] 退款测试

#### 2. 集成测试
- [ ] 完整支付流程测试
- [ ] 异常情况测试（网络中断、重复支付等）
- [ ] 并发测试

#### 3. 安全测试
- [ ] 签名验证测试
- [ ] 防重放攻击测试
- [ ] 金额篡改测试

### 阶段五：上线部署（1天）

#### 1. 生产环境配置
- [ ] 配置生产环境支付密钥
- [ ] 配置HTTPS证书
- [ ] 配置支付回调域名白名单

#### 2. 监控告警
- [ ] 支付成功率监控
- [ ] 支付异常告警
- [ ] 订单状态监控

---

## 💻 技术实现示例

### 1. 后端支付服务（使用Ping++）

```python
# backend/app/services/payment_gateway.py
import pingpp
from app.core.config import settings

class PaymentGateway:
    def __init__(self):
        pingpp.api_key = settings.PAYMENT_API_KEY
        
    def create_charge(self, order_id: str, amount: int, channel: str, 
                     subject: str, body: str, client_ip: str):
        """创建支付订单"""
        charge = pingpp.Charge.create(
            order_no=order_id,
            amount=amount,  # 单位：分
            app=dict(id=settings.PAYMENT_APP_ID),
            channel=channel,  # alipay_qr, wx_pub_qr等
            currency='cny',
            client_ip=client_ip,
            subject=subject,
            body=body,
            extra={
                # 渠道特定参数
            }
        )
        return charge
        
    def query_charge(self, charge_id: str):
        """查询支付状态"""
        return pingpp.Charge.retrieve(charge_id)
        
    def create_refund(self, charge_id: str, amount: int, description: str):
        """创建退款"""
        refund = pingpp.Refund.create(
            charge=charge_id,
            amount=amount,
            description=description
        )
        return refund
```

### 2. 支付回调处理

```python
# backend/app/api/v1/endpoints/payments.py
@router.post("/callback/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """处理支付网关回调"""
    # 获取原始请求体
    raw_data = await request.body()
    signature = request.headers.get('X-Pingplusplus-Signature')
    
    # 验证签名
    if not verify_signature(raw_data, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 解析事件
    event = json.loads(raw_data)
    
    if event['type'] == 'charge.succeeded':
        # 支付成功
        charge = event['data']['object']
        order_id = charge['order_no']
        
        # 更新订单状态
        transaction = db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.transaction_id == order_id
        ).first()
        
        if transaction:
            transaction.status = 'success'
            transaction.gateway_transaction_id = charge['id']
            transaction.callback_received_at = datetime.utcnow()
            
            # 激活订阅
            subscription = transaction.subscription
            subscription.status = 'active'
            
            db.commit()
    
    return {"status": "success"}
```

### 3. 前端支付组件

```typescript
// frontend/src/components/Payment/PaymentQRCode.tsx
import React, { useEffect, useState } from 'react'
import { Modal, QRCode, Spin, Result } from 'antd'

interface PaymentQRCodeProps {
  visible: boolean
  orderId: string
  amount: number
  onSuccess: () => void
  onCancel: () => void
}

const PaymentQRCode: React.FC<PaymentQRCodeProps> = ({
  visible, orderId, amount, onSuccess, onCancel
}) => {
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [status, setStatus] = useState<'pending' | 'success' | 'failed'>('pending')
  
  useEffect(() => {
    if (visible && orderId) {
      // 获取支付二维码
      fetchPaymentQRCode()
      // 开始轮询支付状态
      startPolling()
    }
  }, [visible, orderId])
  
  const fetchPaymentQRCode = async () => {
    const response = await paymentService.getPaymentQRCode(orderId)
    setQrCodeUrl(response.qr_code_url)
  }
  
  const startPolling = () => {
    const interval = setInterval(async () => {
      const result = await paymentService.checkPaymentStatus(orderId)
      if (result.status === 'success') {
        setStatus('success')
        clearInterval(interval)
        setTimeout(onSuccess, 2000)
      } else if (result.status === 'failed') {
        setStatus('failed')
        clearInterval(interval)
      }
    }, 3000)
    
    // 5分钟后停止轮询
    setTimeout(() => clearInterval(interval), 300000)
  }
  
  return (
    <Modal
      title="扫码支付"
      open={visible}
      onCancel={onCancel}
      footer={null}
    >
      {status === 'pending' && (
        <div className="text-center">
          <QRCode value={qrCodeUrl} size={256} />
          <p className="mt-4">请使用支付宝/微信扫码支付</p>
          <p className="text-2xl font-bold">¥{amount}</p>
          <Spin className="mt-4" tip="等待支付..." />
        </div>
      )}
      {status === 'success' && (
        <Result status="success" title="支付成功！" />
      )}
      {status === 'failed' && (
        <Result status="error" title="支付失败" />
      )}
    </Modal>
  )
}
```

---

## 🧪 测试方案

### 沙箱测试账号

#### 支付宝沙箱
- 买家账号：在支付宝开放平台获取
- 测试金额：任意金额
- 测试卡号：支付宝提供的测试账号

#### 微信支付沙箱
- 使用微信支付提供的沙箱环境
- 测试金额：特定金额触发不同场景

### 测试用例

```typescript
// 测试用例清单
const testCases = [
  '正常支付流程',
  '支付超时',
  '支付取消',
  '重复支付',
  '金额不符',
  '签名验证失败',
  '网络中断恢复',
  '并发支付',
  '退款流程',
  '部分退款'
]
```

---

## 📊 预估工作量

| 阶段 | 工作内容 | 预估时间 | 负责人 |
|------|----------|----------|--------|
| 准备 | 注册账号、获取密钥 | 1-2天 | 运营/开发 |
| 后端 | 支付服务开发 | 3-5天 | 后端开发 |
| 前端 | 支付界面开发 | 2-3天 | 前端开发 |
| 测试 | 功能测试、安全测试 | 2-3天 | 测试工程师 |
| 部署 | 生产环境配置 | 1天 | 运维 |
| **总计** | | **9-14天** | |

---

## 🔐 安全注意事项

1. **密钥安全**
   - 不要将密钥提交到代码仓库
   - 使用环境变量管理密钥
   - 定期轮换密钥

2. **签名验证**
   - 所有回调必须验证签名
   - 防止重放攻击
   - 验证金额和订单信息

3. **HTTPS**
   - 生产环境必须使用HTTPS
   - 配置SSL证书
   - 强制HTTPS重定向

4. **日志记录**
   - 记录所有支付操作
   - 敏感信息脱敏
   - 保留审计日志

---

## 📞 技术支持

### 推荐的聚合支付平台

1. **Ping++** (https://www.pingxx.com/)
   - 文档完善，SDK丰富
   - 支持多种支付渠道
   - 有免费额度

2. **BeeCloud** (https://beecloud.cn/)
   - 接入简单
   - 价格透明

3. **易宝支付** (https://www.yeepay.com/)
   - 老牌支付公司
   - 稳定性好

### 开发文档
- Ping++ 文档：https://www.pingxx.com/docs/
- 支付宝开放平台：https://open.alipay.com/
- 微信支付文档：https://pay.weixin.qq.com/wiki/doc/api/

---

## 下一步行动

1. **立即行动**
   - [ ] 选择支付服务商
   - [ ] 注册账号并完成认证
   - [ ] 获取测试环境密钥

2. **本周完成**
   - [ ] 后端支付服务开发
   - [ ] 前端支付界面开发
   - [ ] 沙箱环境测试

3. **下周完成**
   - [ ] 生产环境部署
   - [ ] 真实交易测试
   - [ ] 上线运营

