# pPQR 审批功能修复总结

## 问题描述

用户反馈：即使在审批流程管理中已经配置了"pPQR标准审批流程"，pPQR 列表页仍然无法显示"提交审批"按钮。

## 根本原因分析

通过对比 WPS、PQR 和 pPQR 的实现，发现了以下问题：

### 1. 前端 TypeScript 接口缺失审批字段

**问题：**
- `frontend/src/services/pqr.ts` 中的 `PQRSummary` 接口缺少审批相关字段
- `frontend/src/services/ppqr.ts` 中的 `PPQRSummary` 接口缺少审批相关字段
- 而 `frontend/src/services/wps.ts` 中的 `WPSSummary` 接口有完整的审批字段

**影响：**
虽然后端返回了 `can_submit_approval`、`can_approve` 等字段，但前端 TypeScript 接口没有定义这些字段，导致类型检查失败或字段被忽略。

### 2. 详情页硬编码了 canSubmit 逻辑

**问题：**
- `frontend/src/pages/pPQR/PPQRDetail.tsx` 第 423 行：`canSubmit={!ppqrData.approval_instance_id}`
- `frontend/src/pages/PQR/PQRDetail.tsx` 第 503 行：`canSubmit={!pqrData.approval_instance_id}`

**影响：**
详情页没有使用后端返回的 `can_submit_approval` 字段，而是简单判断是否有审批实例。这导致即使在个人工作区（不支持审批），按钮也会显示。

### 3. 详情页后端接口缺少审批权限字段

**问题：**
- `backend/app/api/v1/endpoints/ppqr.py` 的 `get_ppqr_detail` 接口没有返回 `can_submit_approval` 和 `can_approve`
- `backend/app/api/v1/endpoints/pqr.py` 的 `read_pqr_by_id` 接口也没有返回这些字段

**影响：**
详情页无法获取正确的审批权限信息。

### 4. 审批取消功能的参数问题

**问题：**
- `backend/app/api/v1/endpoints/approvals.py` 的 `cancel_approval` 接口要求 `comment` 参数必填
- 前端可能传递空字符串，导致 400 错误

## 修复方案

### 修复 1：添加前端 TypeScript 接口的审批字段

**文件：** `frontend/src/services/pqr.ts`

```typescript
export interface PQRSummary {
  id: number
  title: string
  pqr_number: string
  revision: string
  status: string
  test_date?: string
  qualification_result?: string
  created_at: string
  updated_at: string
  // 审批相关字段
  approval_instance_id?: number
  approval_status?: string
  workflow_name?: string
  submitter_id?: number
  can_submit_approval?: boolean
  can_approve?: boolean
}
```

**文件：** `frontend/src/services/ppqr.ts`

```typescript
export interface PPQRSummary {
  id: number
  title: string
  ppqr_number: string
  revision: string
  status: string
  test_date?: string
  test_conclusion?: string
  convert_to_pqr?: string
  created_at: string
  updated_at: string
  // 审批相关字段
  approval_instance_id?: number
  approval_status?: string
  workflow_name?: string
  submitter_id?: number
  can_submit_approval?: boolean
  can_approve?: boolean
}
```

### 修复 2：后端详情接口添加审批权限字段

**文件：** `backend/app/api/v1/endpoints/ppqr.py`

在 `get_ppqr_detail` 函数中添加审批服务逻辑，返回 `can_submit_approval` 和 `can_approve` 字段。

**文件：** `backend/app/api/v1/endpoints/pqr.py`

在 `read_pqr_by_id` 函数中添加审批服务逻辑，返回 `can_submit_approval` 和 `can_approve` 字段。

### 修复 3：前端详情页使用后端返回的审批权限

**文件：** `frontend/src/pages/pPQR/PPQRDetail.tsx`

```typescript
<ApprovalButton
  documentType="ppqr"
  documentId={parseInt(id || '0')}
  documentNumber={ppqrData.ppqr_number}
  documentTitle={ppqrData.title}
  instanceId={ppqrData.approval_instance_id}
  status={ppqrData.approval_status || ppqrData.status}
  canSubmit={ppqrData.can_submit_approval || false}  // 使用后端返回的字段
  canApprove={ppqrData.can_approve || false}         // 使用后端返回的字段
  canCancel={ppqrData.submitter_id === user?.id}
  onSuccess={() => {
    window.location.reload()
  }}
/>
```

**文件：** `frontend/src/pages/PQR/PQRDetail.tsx`

```typescript
<ApprovalButton
  documentType="pqr"
  documentId={parseInt(id || '0')}
  documentNumber={pqrData.pqr_number}
  documentTitle={pqrData.title}
  instanceId={pqrData.approval_instance_id}
  status={pqrData.approval_status || pqrData.status}
  canSubmit={pqrData.can_submit_approval || false}  // 使用后端返回的字段
  canApprove={pqrData.can_approve || false}         // 使用后端返回的字段
  canCancel={pqrData.submitter_id === user?.id}
  onSuccess={() => {
    window.location.reload()
  }}
  size="large"
/>
```

### 修复 4：审批取消功能的参数改为可选

**文件：** `backend/app/api/v1/endpoints/approvals.py`

```python
@router.post("/{instance_id}/cancel")
async def cancel_approval(
    instance_id: int,
    comment: str = Query("", description="取消原因（可选）"),  # 改为可选，默认空字符串
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """取消审批（仅提交人可操作）"""
    approval_service = ApprovalService(db)

    instance = approval_service.cancel_approval(
        instance_id=instance_id,
        current_user=current_user,
        comment=comment if comment else None  # 空字符串转为 None
    )
```

## 验证步骤

### 1. 重启后端服务

```bash
cd backend
# 如果使用虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 重启服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 重新编译前端

```bash
cd frontend
npm run build
# 或者开发模式
npm run dev
```

### 3. 测试步骤

1. **确认在企业工作区**
   - 打开浏览器开发者工具（F12）
   - 在 Console 中执行：`localStorage.getItem('current_workspace')`
   - 确认返回的 JSON 中 `type` 为 `"enterprise"`

2. **测试 pPQR 列表页**
   - 访问 pPQR 列表页
   - 检查每个 pPQR 卡片是否显示"提交审批"按钮
   - 点击"提交审批"按钮，填写备注，提交
   - 确认提交成功，状态变为"审批中"

3. **测试 pPQR 详情页**
   - 打开一个 pPQR 的详情页
   - 检查是否显示"提交审批"按钮
   - 测试提交审批功能

4. **测试 PQR 列表和详情页**
   - 同样测试 PQR 的列表页和详情页

## 常见问题排查

### Q1: 修复后按钮还是不显示？

**检查清单：**
1. ✅ 确认在企业工作区（不是个人工作区）
2. ✅ 清除浏览器缓存（Ctrl+F5 强制刷新）
3. ✅ 检查浏览器控制台是否有 TypeScript 错误
4. ✅ 检查后端日志，确认返回了 `can_submit_approval: true`

### Q2: 提交审批时报 400 错误？

**可能原因：**
- 后端还没有重启，仍在使用旧代码
- 工作区配置不正确

**解决方案：**
1. 重启后端服务
2. 检查后端日志中的错误信息
3. 使用诊断工具：访问 `http://localhost:5173/check_ppqr_workspace.html`

### Q3: 提交审批时报 CORS 错误？

**解决方案：**
- 确认后端配置了正确的 CORS 设置
- 检查 `backend/app/core/config.py` 中的 `DEVELOPMENT` 设置为 `True`
- 重启后端服务

## 技术要点总结

1. **前后端接口一致性**：前端 TypeScript 接口必须与后端返回的数据结构匹配
2. **审批权限判断**：应该由后端统一判断，前端只负责显示
3. **工作区上下文**：审批功能依赖于企业工作区，个人工作区不支持
4. **代码复用**：WPS、PQR、pPQR 应该使用相同的审批逻辑和接口设计

## 修改文件清单

### 后端文件
- ✅ `backend/app/api/v1/endpoints/approvals.py` - 修复取消审批参数
- ✅ `backend/app/api/v1/endpoints/ppqr.py` - 添加详情接口审批字段
- ✅ `backend/app/api/v1/endpoints/pqr.py` - 添加详情接口审批字段

### 前端文件
- ✅ `frontend/src/services/pqr.ts` - 添加 PQRSummary 审批字段
- ✅ `frontend/src/services/ppqr.ts` - 添加 PPQRSummary 审批字段
- ✅ `frontend/src/pages/pPQR/PPQRDetail.tsx` - 使用后端返回的审批权限
- ✅ `frontend/src/pages/PQR/PQRDetail.tsx` - 使用后端返回的审批权限

## 预期结果

修复完成后：
1. ✅ pPQR 列表页显示"提交审批"按钮（企业工作区）
2. ✅ pPQR 详情页显示"提交审批"按钮（企业工作区）
3. ✅ PQR 列表页显示"提交审批"按钮（企业工作区）
4. ✅ PQR 详情页显示"提交审批"按钮（企业工作区）
5. ✅ 个人工作区不显示审批按钮
6. ✅ 取消审批功能正常工作

