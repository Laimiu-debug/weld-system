# 质量管理模块 - 快速参考指南

## 🎯 核心功能

### 1. 列表展示
- **路径**: `/quality`
- **组件**: `frontend/src/pages/Quality/QualityList.tsx`
- **功能**: 展示所有质量检验记录，支持搜索、筛选、分页

### 2. 创建质量检验
- **触发**: 点击"新增质量检验"按钮
- **方式**: 模态框表单
- **必填字段**:
  - 检验编号
  - 检验类型
  - 检验日期
  - 检验员ID

### 3. 编辑质量检验
- **触发**: 点击列表中的"编辑"按钮
- **方式**: 模态框表单（预填充数据）
- **权限**: 需要 `quality.update` 权限

### 4. 查看详情
- **触发**: 点击列表中的"查看详情"按钮
- **方式**: 模态框（只读）
- **显示**: 使用 Descriptions 组件展示完整信息

### 5. 删除质量检验
- **单条删除**: 点击"删除"按钮
- **批量删除**: 选中多条记录后点击"批量删除"
- **权限**: 需要 `quality.delete` 权限
- **确认**: 所有删除操作都需要确认

## 📋 API 端点

### 服务类: `QualityService`
**位置**: `frontend/src/services/quality.ts`

```typescript
// 获取列表
qualityService.getQualityInspectionList(params)

// 获取详情
qualityService.getQualityInspectionById(id, workspaceType, companyId, factoryId)

// 创建
qualityService.createQualityInspection(data, workspaceType, companyId, factoryId)

// 更新
qualityService.updateQualityInspection(id, data, workspaceType, companyId, factoryId)

// 删除
qualityService.deleteQualityInspection(id, workspaceType, companyId, factoryId)

// 批量删除
qualityService.batchDeleteQualityInspections(ids, workspaceType, companyId, factoryId)
```

## 🔍 搜索和筛选

### 搜索框
- 支持按检验编号搜索
- 支持按检验员姓名搜索
- 实时搜索（输入后自动触发）

### 筛选器

**检验类型**:
- 全部类型
- 外观检验 (visual)
- 射线检验 (radiographic)
- 超声波检验 (ultrasonic)
- 磁粉检验 (magnetic_particle)
- 渗透检验 (liquid_penetrant)
- 破坏性检验 (destructive)

**检验结果**:
- 全部结果
- 合格 (pass)
- 不合格 (fail)
- 有条件合格 (conditional)
- 待检验 (pending)

## 📊 表格列说明

| 列名 | 字段 | 说明 |
|------|------|------|
| 检验编号 | inspection_number | 唯一标识 |
| 检验类型 | inspection_type | 带颜色标签 |
| 检验结果 | result | 带图标和颜色 |
| 检验日期 | inspection_date | YYYY-MM-DD 格式 |
| 检验员 | inspector_name | 检验员姓名 |
| 是否合格 | is_qualified | 合格/不合格标签 |
| 缺陷数量 | defects_found | 数字 |
| 操作 | - | 查看/编辑/删除按钮 |

## 🎨 UI 组件

### 颜色标签

**检验类型**:
- 外观检验: 蓝色
- 射线检验: 绿色
- 超声波检验: 橙色
- 磁粉检验: 紫色
- 渗透检验: 青色
- 破坏性检验: 红色

**检验结果**:
- 合格: 绿色 + ✓ 图标
- 不合格: 红色 + ✗ 图标
- 有条件合格: 黄色 + ⚠ 图标
- 待检验: 灰色 + 🕐 图标

## 🔐 权限要求

| 操作 | 权限 | 说明 |
|------|------|------|
| 查看列表 | quality.read | 基础权限 |
| 创建 | quality.create | 显示"新增"按钮 |
| 编辑 | quality.update | 显示"编辑"按钮 |
| 删除 | quality.delete | 显示"删除"按钮 |

## 🏢 工作区支持

### 个人工作区
```typescript
{
  workspace_type: 'personal',
  user_id: <当前用户ID>
}
```

### 企业工作区
```typescript
{
  workspace_type: 'enterprise',
  user_id: <当前用户ID>,
  company_id: <企业ID>,
  factory_id: <工厂ID> (可选)
}
```

## 📝 表单字段详解

### 基本信息
- **检验编号** (inspection_number): 必填，唯一标识
- **检验类型** (inspection_type): 必填，下拉选择
- **检验日期** (inspection_date): 必填，日期选择器

### 检验人员
- **检验员ID** (inspector_id): 必填，数字输入
- **检验员姓名** (inspector_name): 可选，文本输入

### 检验结果
- **检验结果** (result): 可选，下拉选择
- **是否合格** (is_qualified): 可选，是/否选择
- **缺陷数量** (defects_found): 可选，数字输入

### 后续处理
- **需要返工** (rework_required): 可选，是/否选择
- **需要跟进** (follow_up_required): 可选，是/否选择
- **纠正措施** (corrective_actions): 可选，多行文本

## 🐛 常见问题

### Q: 为什么看不到"新增"按钮？
A: 检查是否有 `quality.create` 权限

### Q: 为什么无法编辑？
A: 检查是否有 `quality.update` 权限

### Q: 删除后数据还在？
A: 刷新页面或点击"刷新"按钮

### Q: 搜索不生效？
A: 确保输入后按回车或点击搜索按钮

### Q: 批量删除按钮不显示？
A: 需要先选中至少一条记录

## 🔄 数据流程

### 创建流程
```
用户点击"新增" 
→ 打开模态框 
→ 填写表单 
→ 点击"确定" 
→ 调用 createQualityInspection API 
→ 成功后关闭模态框 
→ 刷新列表
```

### 编辑流程
```
用户点击"编辑" 
→ 打开模态框（预填充数据） 
→ 修改表单 
→ 点击"确定" 
→ 调用 updateQualityInspection API 
→ 成功后关闭模态框 
→ 刷新列表
```

### 删除流程
```
用户点击"删除" 
→ 显示确认对话框 
→ 用户确认 
→ 调用 deleteQualityInspection API 
→ 成功后刷新列表
```

## 💡 最佳实践

1. **创建前检查**: 确保检验编号唯一
2. **及时保存**: 填写完表单后立即保存
3. **定期刷新**: 使用刷新按钮获取最新数据
4. **批量操作**: 对于多条记录，使用批量删除提高效率
5. **权限管理**: 根据角色分配适当的权限

## 📞 技术支持

如有问题，请查看：
- 详细文档: `docs/QUALITY_MODULE_IMPLEMENTATION_SUMMARY.md`
- 开发指南: `modules/QUALITY_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 后端API: `backend/app/api/v1/endpoints/quality.py`

---

**版本**: 1.0  
**更新日期**: 2025-10-21

