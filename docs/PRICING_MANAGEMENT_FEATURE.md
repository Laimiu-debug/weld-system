# 订阅计划价格管理功能

## 功能概述

在管理员后台添加了完整的订阅计划价格管理功能，支持设置折扣和降价。

## 新增功能

### 1. 价格管理页面 (`admin-portal/src/pages/PricingManagement.tsx`)

#### 主要功能：
- **查看所有订阅计划**：展示所有订阅计划的详细信息
- **编辑订阅计划**：修改计划名称、描述、价格、配额等
- **设置折扣/降价**：支持两种调价方式

#### 折扣/降价方式：

##### 方式一：按百分比折扣
- 月付折扣：设置0-100%的折扣比例
- 季付折扣：设置0-100%的折扣比例
- 年付折扣：设置0-100%的折扣比例

示例：设置月付10%折扣，原价¥100将变为¥90

##### 方式二：按固定金额降价
- 月付降价：设置固定降价金额
- 季付降价：设置固定降价金额
- 年付降价：设置固定降价金额

示例：设置月付降价¥10，原价¥100将变为¥90

#### 界面特点：
- 清晰展示当前价格和折扣信息
- 实时计算折扣后的价格
- 支持单个计划调价
- 显示推荐标签和启用状态
- 配额限制一目了然

### 2. 后端API接口

#### 已有接口（已启用）：
- `GET /api/v1/admin/membership/subscription-plans` - 获取所有订阅计划
- `PUT /api/v1/admin/membership/subscription-plans/{plan_id}` - 更新订阅计划
- `POST /api/v1/admin/membership/subscription-plans` - 创建订阅计划
- `DELETE /api/v1/admin/membership/subscription-plans/{plan_id}` - 删除订阅计划

#### 新增接口：
- `POST /api/v1/admin/membership/subscription-plans/batch-discount` - 批量设置折扣

##### 批量折扣接口说明：

**请求路径**：`POST /api/v1/admin/membership/subscription-plans/batch-discount`

**权限要求**：超级管理员

**请求体示例**：
```json
{
  "plan_ids": ["personal_pro", "personal_advanced"],
  "discount_type": "percent",
  "monthly_discount": 10,
  "quarterly_discount": 15,
  "yearly_discount": 20
}
```

**参数说明**：
- `plan_ids`: 要调价的订阅计划ID列表
- `discount_type`: 折扣类型，"percent"（百分比）或 "amount"（固定金额）
- `monthly_discount`: 月付折扣值
- `quarterly_discount`: 季付折扣值
- `yearly_discount`: 年付折扣值

**响应示例**：
```json
{
  "success": true,
  "message": "成功调整 2 个订阅计划的价格",
  "data": {
    "updated_count": 2,
    "updated_plans": [
      {
        "plan_id": "personal_pro",
        "plan_name": "个人专业版",
        "original_prices": {
          "monthly": 19.0,
          "quarterly": 51.0,
          "yearly": 183.0
        },
        "new_prices": {
          "monthly": 17.1,
          "quarterly": 43.35,
          "yearly": 146.4
        }
      }
    ]
  }
}
```

### 3. 前端API服务更新

在 `admin-portal/src/services/api.ts` 中添加了以下方法：

```typescript
// 获取订阅计划列表
async getSubscriptionPlans()

// 更新订阅计划
async updateSubscriptionPlan(planId: string, data: any)

// 创建订阅计划
async createSubscriptionPlan(data: any)
```

### 4. 路由和菜单配置

#### 新增菜单项：
- 菜单名称：**价格管理**
- 图标：TagsOutlined
- 路径：`/pricing`

#### 路由配置：
- 路径：`/pricing`
- 组件：`PricingManagement`

## 使用说明

### 访问价格管理页面

1. 登录管理员后台
2. 在左侧菜单中点击"价格管理"
3. 进入订阅计划价格管理页面

### 编辑订阅计划

1. 在计划列表中找到要编辑的计划
2. 点击"编辑"按钮
3. 修改计划信息（名称、描述、价格、配额等）
4. 点击"确定"保存

### 设置折扣/降价

1. 在计划列表中找到要调价的计划
2. 点击"调价"按钮
3. 选择调价方式：
   - **按百分比折扣**：输入折扣百分比（0-100）
   - **按固定金额降价**：输入降价金额
4. 点击"应用调价"

### 注意事项

1. **权限要求**：只有超级管理员可以修改订阅计划价格
2. **价格保护**：降价后的价格不会低于0
3. **精度控制**：价格自动保留两位小数
4. **操作日志**：所有价格调整都会记录到系统日志
5. **优先级**：如果同时设置百分比折扣和固定金额降价，固定金额降价优先

## 技术实现

### 前端技术栈
- React + TypeScript
- Ant Design UI组件库
- React Router路由管理
- Axios HTTP客户端

### 后端技术栈
- FastAPI框架
- SQLAlchemy ORM
- PostgreSQL数据库
- JWT认证

### 数据模型

订阅计划表 (`subscription_plans`)：
- `id`: 计划ID
- `name`: 计划名称
- `description`: 计划描述
- `monthly_price`: 月付价格
- `quarterly_price`: 季付价格
- `yearly_price`: 年付价格
- `currency`: 货币单位
- `max_wps_files`: WPS文件配额
- `max_pqr_files`: PQR文件配额
- `max_ppqr_files`: pPQR文件配额
- `max_materials`: 焊材配额
- `max_welders`: 焊工配额
- `max_equipment`: 设备配额
- `max_factories`: 工厂配额
- `max_employees`: 员工配额
- `features`: 功能列表
- `sort_order`: 排序
- `is_recommended`: 是否推荐
- `is_active`: 是否启用
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 文件清单

### 新增文件
1. `admin-portal/src/pages/PricingManagement.tsx` - 价格管理页面

### 修改文件
1. `admin-portal/src/services/api.ts` - 添加订阅计划管理API方法
2. `admin-portal/src/components/Layout.tsx` - 添加价格管理菜单项
3. `admin-portal/src/App.tsx` - 添加价格管理路由
4. `backend/app/api/v1/api.py` - 启用membership_admin路由
5. `backend/app/api/v1/endpoints/membership_admin.py` - 添加批量折扣API

## 后续优化建议

1. **批量操作**：支持同时调整多个计划的价格
2. **价格历史**：记录价格变更历史，支持回滚
3. **促销活动**：支持设置限时促销活动
4. **价格预览**：在应用前预览调价效果
5. **通知功能**：价格调整后自动通知相关用户
6. **数据导出**：支持导出价格调整报表

## 测试建议

1. 测试单个计划的价格编辑
2. 测试按百分比折扣功能
3. 测试按固定金额降价功能
4. 测试价格保护（不低于0）
5. 测试权限控制（非超级管理员无法操作）
6. 测试操作日志记录
7. 测试批量折扣API

## 常见问题

### Q: 如何恢复原价？
A: 在编辑模式下手动输入原价，或者查看操作日志获取历史价格。

### Q: 折扣和降价可以同时使用吗？
A: 可以同时设置，但固定金额降价会优先生效。

### Q: 价格调整会影响现有订阅吗？
A: 不会。价格调整只影响新订阅，现有订阅保持原价格。

### Q: 如何批量调整所有计划的价格？
A: 使用批量折扣API，传入所有计划的ID列表。

## 联系支持

如有问题或建议，请联系开发团队。

