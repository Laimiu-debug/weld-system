# 仪表盘数据统计失真问题修复报告

## 问题描述

用户 `testuser176070001` 在企业工作区中看到的实际数据与仪表盘统计数据不一致：

### 实际数据（列表页面显示）
- WPS: 4个
- PQR: 3个
- pPQR: 2个
- 焊工: 1个

### 仪表盘统计数据（错误）
- WPS: 14个
- PQR: 4个
- pPQR: 2个
- 焊工: 5个

### 差异
- WPS: 多统计了 10 条已删除记录
- PQR: 多统计了 1 条已删除记录
- pPQR: 正确
- 焊工: 多统计了 4 条已删除记录

## 问题根源

在 `backend/app/services/dashboard_service.py` 中，仪表盘统计查询**没有过滤 `is_active` 字段**，导致已删除的记录（`is_active=False`）也被统计在内。

### 问题代码位置

1. **个人工作区统计** (`_get_personal_stats` 方法，第54-103行)
   - WPS、PQR、pPQR、焊材、焊工、设备、生产任务、质量检验统计都缺少 `is_active=True` 过滤

2. **企业工作区统计** (`_get_enterprise_stats` 方法，第134-194行)
   - WPS、PQR、pPQR、焊材、焊工、设备、生产任务、质量检验统计都缺少 `is_active=True` 过滤

## 修复方案

在所有统计查询中添加 `is_active=True` 过滤条件。

### 修复前的代码示例
```python
# WPS统计
wps_count = self.db.query(func.count(WPS.id)).filter(
    WPS.company_id == workspace_context.company_id,
    WPS.workspace_type == WorkspaceType.ENTERPRISE
).scalar() or 0
```

### 修复后的代码示例
```python
# WPS统计
wps_count = self.db.query(func.count(WPS.id)).filter(
    WPS.company_id == workspace_context.company_id,
    WPS.workspace_type == WorkspaceType.ENTERPRISE,
    WPS.is_active == True  # 添加此过滤条件
).scalar() or 0
```

## 修复内容

### 1. 个人工作区统计修复
在 `_get_personal_stats` 方法中，为以下统计添加 `is_active=True` 过滤：
- WPS 统计
- PQR 统计
- pPQR 统计
- 焊材统计
- 焊工统计
- 设备统计
- 生产任务统计
- 质量检验统计

### 2. 企业工作区统计修复
在 `_get_enterprise_stats` 方法中，为以下统计添加 `is_active=True` 过滤：
- WPS 统计
- PQR 统计
- pPQR 统计
- 焊材统计
- 焊工统计
- 设备统计
- 生产任务统计
- 质量检验统计

## 验证结果

运行验证脚本 `verify_dashboard_fix.py` 后的结果：

```
=== 仪表盘统计结果（修复后） ===
WPS: 4
PQR: 3
pPQR: 2
焊工: 1
焊材: 2
设备: 4
生产任务: 1
质量检验: 0

=== 预期结果 ===
WPS: 4
PQR: 3
pPQR: 2
焊工: 1

=== 验证结果 ===
✓ 修复成功！仪表盘统计数据正确
```

## 已删除记录详情

通过 `check_dashboard_is_active.py` 脚本发现的已删除记录：

### WPS (10条已删除记录)
- WPS-1761151710423 (ID: 2)
- WPS-1761151576046 (ID: 1)
- 998-COPY-1761154673420 (ID: 6)
- 998-COPY-1761156193418 (ID: 7)
- 003 (ID: 8)
- WPS-1761393991580 (ID: 40)
- 111 (ID: 39)
- WPS-1761546670373 (ID: 41)
- WPS-1761546728148-COPY-1761547079576 (ID: 43)
- WPS-1761546728148-COPY-1761547670803 (ID: 44)

### PQR (1条已删除记录)
- 856 (ID: 8)

### 焊工 (4条已删除记录)
- 454 殷光辉 (ID: 5)
- 22 抖音 (ID: 6)
- 336 ggg (ID: 7)
- 36 99 (ID: 8)

## 相关文件

### 修复的文件
- `backend/app/services/dashboard_service.py`

### 诊断脚本
- `backend/check_dashboard_is_active.py` - 检查 is_active 字段影响的脚本
- `backend/verify_dashboard_fix.py` - 验证修复结果的脚本

## 其他服务的状态

检查发现其他服务已经正确实现了 `is_active` 过滤：
- ✓ `wps_service.py` - 已正确过滤
- ✓ `pqr_service.py` - 已正确过滤
- ✓ `ppqr_service.py` - 已正确过滤
- ✓ `welder_service.py` - 已正确过滤

## 影响范围

此修复影响所有使用仪表盘统计功能的用户：
- 个人工作区用户
- 企业工作区用户

修复后，仪表盘将只显示活跃记录（`is_active=True`）的统计数据，不再包含已删除的记录。

## 建议

1. **数据一致性检查**：建议定期检查所有统计查询是否正确过滤 `is_active` 字段
2. **代码审查**：在添加新的统计功能时，确保包含 `is_active=True` 过滤条件
3. **测试覆盖**：添加单元测试确保统计功能正确过滤已删除记录

## 修复日期

2025-10-27

## 修复人员

AI Assistant (Augment Agent)

