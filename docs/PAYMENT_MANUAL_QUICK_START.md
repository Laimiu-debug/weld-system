# 个人收款码支付 - 1小时快速开始

> 完全免费，零手续费，1小时内上线

---

## 🎯 方案概述

**个人收款码支付方案**
- ✅ **完全免费** - 0手续费，0成本
- ✅ **快速上线** - 1小时内完成
- ✅ **安全可靠** - 使用官方收款码
- ✅ **适合起步** - 0-100用户阶段

**流程：**
1. 用户选择套餐 → 2. 显示收款码 → 3. 用户扫码支付 → 4. 提交交易号 → 5. 管理员确认 → 6. 开通会员

---

## 📦 已为您创建的文件

### 前端文件
1. **`frontend/src/components/Payment/ManualPaymentModal.tsx`** ⭐
   - 手动支付弹窗组件
   - 显示收款二维码
   - 收集支付凭证
   - 三步引导流程

2. **`frontend/src/pages/Admin/PendingPayments.tsx`** ⭐
   - 管理后台待确认列表
   - 确认/拒绝支付
   - 查看支付详情

### 后端接口（需要添加）
- `POST /api/v1/payments/manual-confirm` - 提交支付凭证
- `GET /api/v1/payments/pending` - 获取待确认列表
- `POST /api/v1/payments/admin/confirm-payment` - 确认支付
- `POST /api/v1/payments/admin/reject-payment` - 拒绝支付

---

## 🚀 1小时快速开始

### 第1步：准备收款码（10分钟）

#### 支付宝收款码

```bash
1. 打开支付宝APP
2. 首页点击"收钱"
3. 点击右上角"..."
4. 选择"保存图片"
5. 将图片重命名为 alipay.jpg
```

#### 微信收款码

```bash
1. 打开微信APP
2. 点击右上角"+"
3. 选择"收付款" → "二维码收款"
4. 点击"保存收款码"
5. 将图片重命名为 wechat.jpg
```

#### 上传收款码

```bash
# 创建目录
mkdir -p frontend/public/qrcode

# 复制收款码图片
# 将 alipay.jpg 和 wechat.jpg 复制到 frontend/public/qrcode/
```

---

### 第2步：添加后端接口（20分钟）

创建文件 `backend/app/api/v1/endpoints/manual_payments.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.api import deps
from app.models.user import User
from app.models.subscription import SubscriptionTransaction, Subscription
from app.schemas.payment import ManualPaymentRequest

router = APIRouter()


@router.post("/manual-confirm")
async def submit_manual_payment(
    request: ManualPaymentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """提交手动支付凭证"""
    
    # 查找订单
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.order_id == request.order_id,
        SubscriptionTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if transaction.status != 'pending':
        raise HTTPException(status_code=400, detail="订单状态不正确")
    
    # 保存支付凭证
    transaction.transaction_id = request.transaction_id
    transaction.payment_method = request.payment_method
    transaction.status = 'pending_confirm'  # 待确认
    transaction.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": "支付凭证已提交，请等待确认"
    }


@router.get("/pending")
async def get_pending_payments(
    status: str = 'pending_confirm',
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin)
):
    """获取待确认支付列表（管理员）"""
    
    query = db.query(SubscriptionTransaction).join(User)
    
    if status != 'all':
        query = query.filter(SubscriptionTransaction.status == status)
    
    transactions = query.order_by(
        SubscriptionTransaction.created_at.desc()
    ).all()
    
    return [
        {
            "order_id": t.order_id,
            "user_id": t.user_id,
            "user_name": t.user.username,
            "user_email": t.user.email,
            "plan_id": t.plan_id,
            "plan_name": t.plan.name,
            "amount": float(t.amount),
            "payment_method": t.payment_method,
            "transaction_id": t.transaction_id,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in transactions
    ]


@router.post("/admin/confirm-payment")
async def confirm_manual_payment(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin)
):
    """管理员确认手动支付"""
    
    # 查找订单
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.order_id == order_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if transaction.status != 'pending_confirm':
        raise HTTPException(status_code=400, detail="订单状态不正确")
    
    # 更新订单状态
    transaction.status = 'success'
    transaction.paid_at = datetime.utcnow()
    transaction.updated_at = datetime.utcnow()
    
    # 激活订阅
    subscription = db.query(Subscription).filter(
        Subscription.id == transaction.subscription_id
    ).first()
    
    if subscription:
        subscription.status = 'active'
        subscription.activated_at = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: 发送邮件通知用户
    
    return {
        "success": True,
        "message": "支付已确认，会员已开通"
    }


@router.post("/admin/reject-payment")
async def reject_manual_payment(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin)
):
    """管理员拒绝手动支付"""
    
    # 查找订单
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.order_id == order_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 更新订单状态
    transaction.status = 'rejected'
    transaction.updated_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: 发送邮件通知用户
    
    return {
        "success": True,
        "message": "支付已拒绝"
    }
```

#### 注册路由

编辑 `backend/app/api/v1/api.py`，添加：

```python
from app.api.v1.endpoints import manual_payments

api_router.include_router(
    manual_payments.router,
    prefix="/payments",
    tags=["payments"]
)
```

---

### 第3步：集成到会员升级页面（15分钟）

编辑 `frontend/src/pages/Membership/MembershipUpgrade.tsx`：

```typescript
import ManualPaymentModal from '@/components/Payment/ManualPaymentModal'

// 添加状态
const [manualPaymentVisible, setManualPaymentVisible] = useState(false)
const [currentOrderId, setCurrentOrderId] = useState('')
const [currentAmount, setCurrentAmount] = useState(0)
const [currentPlanName, setCurrentPlanName] = useState('')
const [currentPaymentMethod, setCurrentPaymentMethod] = useState<'alipay' | 'wechat'>('alipay')

// 修改支付处理函数
const handlePayment = async () => {
  try {
    // 创建订单
    const response = await fetch('/api/v1/payments/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        plan_id: selectedPlan,
        payment_method: paymentMethod
      })
    })

    const data = await response.json()

    if (response.ok) {
      // 显示手动支付弹窗
      setCurrentOrderId(data.order_id)
      setCurrentAmount(data.amount)
      setCurrentPlanName(data.plan_name)
      setCurrentPaymentMethod(paymentMethod as 'alipay' | 'wechat')
      setManualPaymentVisible(true)
    }
  } catch (error) {
    message.error('创建订单失败')
  }
}

// 在 JSX 中添加
<ManualPaymentModal
  visible={manualPaymentVisible}
  orderId={currentOrderId}
  amount={currentAmount}
  planName={currentPlanName}
  paymentMethod={currentPaymentMethod}
  onSuccess={() => {
    setManualPaymentVisible(false)
    navigate('/membership/orders')
  }}
  onCancel={() => setManualPaymentVisible(false)}
/>
```

---

### 第4步：添加管理后台路由（10分钟）

编辑 `frontend/src/App.tsx`，添加：

```typescript
import PendingPayments from '@/pages/Admin/PendingPayments'

// 在路由配置中添加
<Route path="/admin/pending-payments" element={<PendingPayments />} />
```

---

### 第5步：测试（5分钟）

```bash
# 启动后端
cd backend
python -m uvicorn app.main:app --reload

# 启动前端
cd frontend
npm run dev

# 访问测试
http://localhost:3000/membership/upgrade
```

**测试流程：**
1. 选择套餐并点击支付
2. 查看收款二维码
3. 输入测试交易号（如：2025010112000000）
4. 提交凭证
5. 访问 http://localhost:3000/admin/pending-payments
6. 确认支付
7. 验证会员已开通

---

## 📊 完整流程图

```
用户端：
选择套餐 → 点击支付 → 显示收款码 → 扫码支付 → 输入交易号 → 提交凭证 → 等待确认

管理端：
收到通知 → 查看列表 → 核对交易 → 确认支付 → 开通会员 → 发送通知
```

---

## ✅ 检查清单

### 准备阶段
- [ ] 已保存支付宝收款码
- [ ] 已保存微信收款码
- [ ] 已上传到 frontend/public/qrcode/

### 后端开发
- [ ] 已创建 manual_payments.py
- [ ] 已注册路由
- [ ] 已测试接口

### 前端开发
- [ ] ManualPaymentModal 组件已创建
- [ ] PendingPayments 页面已创建
- [ ] 已集成到会员升级页面
- [ ] 已添加管理后台路由

### 测试
- [ ] 用户可以看到收款码
- [ ] 用户可以提交交易号
- [ ] 管理员可以看到待确认列表
- [ ] 管理员可以确认支付
- [ ] 确认后会员自动开通

---

## 🎉 完成！

恭喜！您已经完成了个人收款码支付方案的集成！

**现在您可以：**
- ✅ 接收真实支付
- ✅ 零手续费
- ✅ 完全免费

**下一步：**
- 当用户量增长后，可以升级到 Stripe 等自动化方案
- 月收入稳定后，可以注册公司使用官方支付

需要帮助？查看 `docs/PAYMENT_FREE_SOLUTIONS.md` 了解更多方案！

