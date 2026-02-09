# 🏗️ 完整架构总结

## 📋 文档导航

本项目的数据隔离、权限管理和会员体系架构已完整实现，以下是相关文档：

### 核心架构文档

1. **`DATA_ISOLATION_AND_PERMISSION_ARCHITECTURE.md`** - 数据隔离与权限管理架构
   - 架构概述和设计目标
   - 核心概念（工作区、访问级别、权限结构）
   - 数据隔离实现
   - 权限管理实现
   - 配额管理实现
   - 设备管理模块实现总结

2. **`MEMBERSHIP_AND_QUOTA_SYSTEM.md`** - 会员体系与配额管理系统
   - 双轨会员制（个人/企业）
   - 会员等级配置
   - 配额管理机制
   - 模块分类（文档类/物理资产类）
   - 实现细节和代码示例

3. **`QUICK_IMPLEMENTATION_GUIDE.md`** - 快速实施指南
   - 数据模型模板
   - Schema模板
   - 服务层完整代码
   - 会员体系集成说明

4. **`API_ENDPOINT_TEMPLATE.md`** - API端点模板
   - 完整的API端点代码
   - 工作区上下文构建
   - 错误处理标准
   - 测试建议

5. **`FRIENDLY_ERROR_MESSAGES.md`** - 友好错误提示文档
   - 错误提示优化方案
   - 避免重复显示错误

---

## 🎯 三大核心系统

### 1. 数据隔离系统

```
┌─────────────────────────────────────────┐
│           数据隔离系统                    │
├─────────────────────────────────────────┤
│                                         │
│  个人工作区                              │
│  ├─ workspace_type = "personal"        │
│  ├─ user_id = 当前用户ID                │
│  └─ 只能访问自己创建的数据               │
│                                         │
│  企业工作区                              │
│  ├─ workspace_type = "enterprise"      │
│  ├─ company_id = 企业ID                │
│  ├─ factory_id = 工厂ID（可选）         │
│  └─ 根据权限访问企业数据                 │
│                                         │
└─────────────────────────────────────────┘
```

**关键字段**：
- `workspace_type`：工作区类型
- `user_id`：创建者ID
- `company_id`：企业ID
- `factory_id`：工厂ID
- `access_level`：访问级别（private/factory/company/public）

### 2. 权限管理系统

```
┌─────────────────────────────────────────┐
│           权限管理系统                    │
├─────────────────────────────────────────┤
│                                         │
│  权限检查层次：                          │
│                                         │
│  1️⃣ 企业所有者                          │
│     └─> 所有权限 ✅                     │
│                                         │
│  2️⃣ 企业管理员 (role="admin")           │
│     └─> 所有权限 ✅                     │
│                                         │
│  3️⃣ 角色权限                            │
│     └─> 检查 CompanyRole.permissions   │
│         {                               │
│           "equipment_management": {     │
│             "view": true,               │
│             "create": true,             │
│             "edit": true,               │
│             "delete": true              │
│           }                             │
│         }                               │
│                                         │
│  4️⃣ 默认权限（无角色）                   │
│     ├─> view ✅                         │
│     ├─> create ✅                       │
│     └─> edit/delete 仅限自己的数据      │
│                                         │
└─────────────────────────────────────────┘
```

**数据访问范围**：
- `data_access_scope = "company"`：访问整个企业的数据
- `data_access_scope = "factory"`：只访问所在工厂的数据

### 3. 会员配额系统

```
┌─────────────────────────────────────────┐
│           会员配额系统                    │
├─────────────────────────────────────────┤
│                                         │
│  双轨会员制：                            │
│                                         │
│  个人会员                                │
│  ├─ User.membership_tier               │
│  ├─ 免费版: WPS 10个, PQR 10个, pPQR 0个│
│  ├─ 专业版: WPS/PQR/pPQR 各30个         │
│  ├─ 高级版: WPS/PQR/pPQR 各50个         │
│  └─ 旗舰版: WPS/PQR/pPQR 各100个        │
│                                         │
│  企业会员                                │
│  ├─ Company.membership_tier            │
│  ├─ 企业版: WPS/PQR/pPQR 各200个, 10人  │
│  ├─ 企业PRO版: 各400个, 20人            │
│  └─ 企业PRO MAX版: 各500个, 50人        │
│                                         │
│  模块分类：                              │
│                                         │
│  📄 文档类（受配额限制）                 │
│  ├─ WPS（焊接工艺规程）                 │
│  ├─ PQR（工艺评定记录）                 │
│  └─ pPQR（预工艺评定记录）              │
│                                         │
│  🔧 物理资产类（不受配额限制）           │
│  ├─ 设备管理                            │
│  ├─ 焊材管理                            │
│  ├─ 焊工管理                            │
│  ├─ 生产管理                            │
│  └─ 质量管理                            │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔄 完整业务流程

### 创建资源流程

```
用户发起创建请求
    ↓
1️⃣ 构建工作区上下文
    ├─ workspace_type
    ├─ user_id
    ├─ company_id
    └─ factory_id
    ↓
2️⃣ 检查创建权限（企业工作区）
    ├─ 企业所有者？ → ✅ 通过
    ├─ 企业管理员？ → ✅ 通过
    ├─ 有CREATE权限？ → ✅ 通过
    └─ 无权限 → ❌ 403错误
    ↓
3️⃣ 检查配额
    ├─ 物理资产模块？ → ✅ 跳过检查
    └─ 文档类模块？
        ├─ 个人工作区 → 检查用户配额
        └─ 企业工作区 → 检查企业配额
            ├─ 配额充足？ → ✅ 通过
            └─ 配额不足？ → ❌ 403错误
    ↓
4️⃣ 创建资源
    ├─ 设置数据隔离字段
    │   ├─ workspace_type
    │   ├─ user_id
    │   ├─ company_id
    │   └─ factory_id
    ├─ 设置访问级别
    │   ├─ 个人工作区 → access_level="private"
    │   └─ 企业工作区 → access_level="company"
    └─ 保存到数据库
    ↓
5️⃣ 更新配额使用
    ├─ 物理资产模块？ → ✅ 跳过更新
    └─ 文档类模块？
        ├─ 个人工作区 → user.{module}_usage += 1
        └─ 企业工作区 → company.{module}_usage += 1
    ↓
✅ 返回成功
```

### 查询资源流程

```
用户发起查询请求
    ↓
1️⃣ 构建工作区上下文
    ↓
2️⃣ 检查查看权限
    ├─ 企业所有者？ → data_access_scope="company"
    ├─ 企业管理员？ → data_access_scope="company"
    ├─ 有VIEW权限？ → 获取data_access_scope
    └─ 无权限 → ❌ 403错误
    ↓
3️⃣ 应用数据隔离过滤
    ├─ 个人工作区
    │   └─ WHERE workspace_type='personal' AND user_id=当前用户
    └─ 企业工作区
        ├─ WHERE workspace_type='enterprise' AND company_id=企业ID
        └─ data_access_scope="factory"？
            └─ AND factory_id=工厂ID
    ↓
4️⃣ 应用业务过滤
    ├─ 搜索关键词
    ├─ 状态筛选
    └─ 排序分页
    ↓
✅ 返回结果
```

### 更新/删除资源流程

```
用户发起更新/删除请求
    ↓
1️⃣ 构建工作区上下文
    ↓
2️⃣ 获取资源（含数据隔离过滤）
    ├─ 资源存在？ → 继续
    └─ 资源不存在？ → ❌ 404错误
    ↓
3️⃣ 检查编辑/删除权限
    ├─ 企业所有者？ → ✅ 通过
    ├─ 企业管理员？ → ✅ 通过
    ├─ 有EDIT/DELETE权限？ → ✅ 通过
    ├─ 是创建者？ → ✅ 通过
    └─ 无权限 → ❌ 403错误
    ↓
4️⃣ 执行操作
    ├─ 更新：修改字段
    └─ 删除：设置is_active=False
    ↓
5️⃣ 更新配额使用（仅删除操作）
    ├─ 物理资产模块？ → ✅ 跳过更新
    └─ 文档类模块？
        ├─ 个人工作区 → user.{module}_usage -= 1
        └─ 企业工作区 → company.{module}_usage -= 1
    ↓
✅ 返回成功
```

---

## 📊 数据模型标准

### 所有模块必需字段

```python
class YourModel(Base):
    # ============ 主键 ============
    id = Column(Integer, primary_key=True, index=True)
    
    # ============ 数据隔离字段（必需）============
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True, index=True)
    access_level = Column(String(20), default="private", nullable=False)
    
    # ============ 业务字段 ============
    # 根据实际需求定义
    
    # ============ 审计字段（必需）============
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

---

## 🚀 新模块开发流程

### 1. 确定模块类型

**物理资产类**（设备、焊材、焊工、生产、质量）：
- ✅ 不受配额限制
- ✅ 不需要添加usage字段
- ✅ 仍需调用配额方法（会自动跳过）

**文档类**（WPS、PQR、pPQR）：
- ✅ 受配额限制
- ✅ 需要添加usage字段
- ✅ 需要配置配额限制

### 2. 创建数据模型（5分钟）

复制模板，修改类名和业务字段

### 3. 创建Schema（5分钟）

定义Create、Update、Response Schema

### 4. 创建服务层（15分钟）

复制设备服务代码，修改：
- 类名和模型名
- 权限键名（如`material_management`）
- 配额类型（如`materials`）

### 5. 创建API端点（10分钟）

复制设备端点代码，修改路由和模型

### 6. 注册路由（1分钟）

在`api.py`中添加路由

### 7. 创建数据库迁移（5分钟）

```bash
alembic revision --autogenerate -m "Add {module} table"
alembic upgrade head
```

### 8. 测试（10分钟）

- 个人工作区CRUD
- 企业工作区CRUD
- 权限测试

**总计：约50分钟完成一个新模块！**

---

## ✅ 实施检查清单

### 数据模型
- [ ] 包含所有数据隔离字段
- [ ] 包含审计字段
- [ ] 添加必要的索引
- [ ] 在base.py中注册

### 服务层
- [ ] 初始化DataAccessMiddleware和QuotaService
- [ ] 实现create方法（权限检查、配额检查、设置隔离字段）
- [ ] 实现get_list方法（权限检查、数据过滤）
- [ ] 实现get_by_id方法（数据隔离、权限检查）
- [ ] 实现update方法（获取数据、权限检查、更新）
- [ ] 实现delete方法（获取数据、权限检查、软删除、更新配额）

### API端点
- [ ] 实现所有CRUD端点
- [ ] 统一错误处理
- [ ] 统一响应格式
- [ ] 在api.py中注册路由

### 权限配置
- [ ] 在CompanyRole.permissions中添加模块权限
- [ ] 测试各种权限场景

### 会员配额（仅文档类模块）
- [ ] 在User表添加{module}_usage字段
- [ ] 在Company表添加{module}_usage字段
- [ ] 在PERSONAL_TIERS配置配额
- [ ] 在ENTERPRISE_TIERS配置配额
- [ ] 测试配额限制

---

## 🎯 关键要点

### 必须遵守的规则

1. **数据隔离字段**：所有模块必须包含相同的隔离字段
2. **审计字段**：所有模块必须包含审计字段
3. **权限检查顺序**：企业所有者 > 管理员 > 角色权限 > 默认权限
4. **访问级别设置**：个人工作区=private，企业工作区=company
5. **配额方法调用**：所有模块都需要调用（QuotaService会自动判断）
6. **错误提示格式**：`"权限不足：具体原因"`
7. **前端错误处理**：避免重复显示错误

### 灵活调整的部分

1. **业务字段**：根据实际需求定义
2. **搜索过滤**：根据业务需求添加
3. **排序规则**：根据业务需求调整
4. **默认权限**：可以根据业务需求调整

---

## 📚 后续模块实施顺序

### 推荐顺序

1. **焊材管理** → 最简单，验证架构可复用性
2. **焊工管理** → 增加证书管理，验证架构灵活性
3. **生产管理** → 涉及多模块关联，验证架构扩展性
4. **质量管理** → 与生产关联，完善业务闭环

---

## 🎉 总结

通过这套完整的架构体系，我们实现了：

✅ **数据隔离**：个人和企业数据完全隔离
✅ **权限管理**：基于角色的细粒度权限控制
✅ **会员配额**：灵活的双轨会员制度
✅ **统一架构**：所有模块使用相同的模式
✅ **易于扩展**：新模块可以快速实现
✅ **安全可靠**：多层权限检查，确保数据安全

**现在你可以快速、安全地实现所有业务模块了！** 🚀

