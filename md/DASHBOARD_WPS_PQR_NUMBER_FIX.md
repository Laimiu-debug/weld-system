# 仪表盘WPS和PQR编号显示修复

## 问题描述

在仪表盘的"最近WPS记录"和"最近PQR记录"模块中，编号列显示为空白，无法看到WPS编号和PQR编号。

## 问题分析

### 1. 前端期望的数据结构

前端表格列配置：

```typescript
// WPS表格列
const wpsColumns = [
  {
    title: 'WPS编号',
    dataIndex: 'wps_number',  // 期望字段名
    key: 'wps_number',
    render: (text: string, record: WPSRecord) => (
      <Button type="link" onClick={() => navigate(`/wps/${record.id}`)}>
        {text}
      </Button>
    ),
  },
  // ...
]

// PQR表格列
const pqrColumns = [
  {
    title: 'PQR编号',
    dataIndex: 'pqr_number',  // 期望字段名
    key: 'pqr_number',
    render: (text: string, record: PQRRecord) => (
      <Button type="link" onClick={() => navigate(`/pqr/${record.id}`)}>
        {text}
      </Button>
    ),
  },
  // ...
]
```

### 2. 后端原来返回的数据结构

**文件**: `backend/app/services/dashboard_service.py`

```python
# WPS记录
activities.append({
    "type": "wps",
    "id": wps.id,
    "title": wps.wps_number,        # ❌ 编号放在了title字段
    "description": wps.title or "WPS记录",
    "status": wps.status,
    "created_at": wps.created_at.isoformat()
})

# PQR记录
activities.append({
    "type": "pqr",
    "id": pqr.id,
    "title": pqr.pqr_number,        # ❌ 编号放在了title字段
    "description": pqr.title or "PQR记录",
    "status": pqr.status,
    "created_at": pqr.created_at.isoformat()
})
```

### 3. 根本原因

后端返回的数据结构中：
- `title` 字段存储的是编号（`wps_number` 或 `pqr_number`）
- `description` 字段存储的是实际的标题

但前端期望：
- `wps_number` 或 `pqr_number` 字段存储编号
- `title` 字段存储标题

导致前端无法从`wps_number`或`pqr_number`字段获取数据，显示为空白。

## 修复方案

### 1. 修改后端返回的数据结构

**文件**: `backend/app/services/dashboard_service.py`

#### WPS记录修复

```python
for wps in wps_query:
    activities.append({
        "type": "wps",
        "id": wps.id,
        "wps_number": wps.wps_number,  # ✅ 添加wps_number字段
        "title": wps.title or "WPS记录",  # ✅ title存储实际标题
        "description": wps.title or "WPS记录",
        "status": wps.status,
        "created_at": wps.created_at.isoformat() if wps.created_at else None,
        "updated_at": wps.updated_at.isoformat() if wps.updated_at else None  # ✅ 添加updated_at
    })
```

#### PQR记录修复

```python
for pqr in pqr_query:
    activities.append({
        "type": "pqr",
        "id": pqr.id,
        "pqr_number": pqr.pqr_number,  # ✅ 添加pqr_number字段
        "title": pqr.title or "PQR记录",  # ✅ title存储实际标题
        "description": pqr.title or "PQR记录",
        "status": pqr.status,
        "qualification_date": pqr.qualification_date.isoformat() if pqr.qualification_date else None,  # ✅ 添加qualification_date
        "created_at": pqr.created_at.isoformat() if pqr.created_at else None,
        "updated_at": pqr.updated_at.isoformat() if pqr.updated_at else None  # ✅ 添加updated_at
    })
```

### 2. 更新前端类型定义

**文件**: `frontend/src/services/dashboard.ts`

```typescript
export interface RecentActivity {
  type: string
  id: number
  wps_number?: string        // ✅ 添加WPS编号字段
  pqr_number?: string        // ✅ 添加PQR编号字段
  title: string
  description: string
  status: string
  qualification_date?: string  // ✅ 添加PQR鉴定日期
  created_at: string
  updated_at?: string        // ✅ 添加更新时间
}
```

## 验证结果

### API返回的数据示例

```json
[
  {
    "type": "wps",
    "id": 44,
    "wps_number": "WPS-1761546728148-COPY-1761547670803",  // ✅ 编号字段
    "title": "WPS-1761546728148 (副本)",                    // ✅ 标题字段
    "description": "WPS-1761546728148 (副本)",
    "status": "draft",
    "created_at": "2025-10-27T06:47:50.821304",
    "updated_at": "2025-10-27T06:47:54.225452"
  },
  {
    "type": "pqr",
    "id": 11,
    "pqr_number": "333333333-COPY-1761548816",  // ✅ 编号字段
    "title": "PQR测试001 (副本)",                // ✅ 标题字段
    "description": "PQR测试001 (副本)",
    "status": "draft",
    "qualification_date": null,
    "created_at": "2025-10-27T07:06:56.460043",
    "updated_at": "2025-10-27T07:06:56.460046"
  }
]
```

### 前端显示效果

现在仪表盘中：
- **WPS编号列**：正确显示WPS编号（如：`WPS-1761546728148-COPY-1761547670803`）
- **PQR编号列**：正确显示PQR编号（如：`333333333-COPY-1761548816`）
- **标题列**：正确显示标题（如：`WPS-1761546728148 (副本)`）
- **状态列**：正确显示状态标签
- **更新时间列**：正确显示更新时间

## 相关文件

- `backend/app/services/dashboard_service.py` - 仪表盘服务（修改数据结构）
- `frontend/src/services/dashboard.ts` - 仪表盘服务类型定义（更新接口）
- `frontend/src/pages/Dashboard/index.tsx` - 仪表盘页面（表格列配置）

## 修复日期

2025-10-27

## 额外改进

除了修复编号显示问题，还添加了以下字段：
1. **updated_at** - 更新时间，用于显示记录的最后修改时间
2. **qualification_date** - PQR鉴定日期，用于显示PQR的鉴定日期

这些字段可以在未来用于增强仪表盘的显示功能。

