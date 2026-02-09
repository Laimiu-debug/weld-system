# 💎 会员等级配置更正说明

## 📋 更正内容

根据实际的会员体系配置，已更新所有文档中的会员等级信息。

---

## ✅ 正确的会员等级配置

### 个人会员等级

| 等级代码 | 等级名称 | 价格 | WPS配额 | PQR配额 | pPQR配额 |
|---------|---------|------|---------|---------|----------|
| `free` | 个人免费版 | 免费 | 10 | 10 | 0（不支持） |
| `personal_pro` | 个人专业版 | ¥19/月 | 30 | 30 | 30 |
| `personal_advanced` | 个人高级版 | ¥49/月 | 50 | 50 | 50 |
| `personal_flagship` | 个人旗舰版 | ¥99/月 | 100 | 100 | 100 |

**关键点**：
- ✅ 个人免费版**不支持pPQR功能**（配额为0）
- ✅ 个人专业版及以上等级的WPS、PQR、pPQR配额**完全相同**
- ✅ 没有"基础版"、"无限版"等级

### 企业会员等级

| 等级代码 | 等级名称 | 价格 | WPS配额 | PQR配额 | pPQR配额 | 多工厂数量 |
|---------|---------|------|---------|---------|----------|-----------|
| `enterprise` | 企业版 | ¥199/月 | 200 | 200 | 200 | 10人 |
| `enterprise_pro` | 企业版PRO | ¥399/月 | 400 | 400 | 400 | 20人 |
| `enterprise_pro_max` | 企业版PRO MAX | ¥899/月 | 500 | 500 | 500 | 50人 |

**关键点**：
- ✅ 企业版的基础等级是`enterprise`（不是`enterprise_basic`）
- ✅ 没有"企业无限版"
- ✅ 企业版包含**多工厂数量**（员工数）限制

---

## 🔧 代码配置

### 后端配置（backend/app/core/config.py）

```python
# 个人会员等级配置
PERSONAL_TIERS = {
    "free": {
        "name": "个人免费版",
        "price": "免费",
        "wps_quota": 10,
        "pqr_quota": 10,
        "ppqr_quota": 0  # 免费版不支持pPQR
    },
    "personal_pro": {
        "name": "个人专业版",
        "price": "¥19/月",
        "wps_quota": 30,
        "pqr_quota": 30,
        "ppqr_quota": 30
    },
    "personal_advanced": {
        "name": "个人高级版",
        "price": "¥49/月",
        "wps_quota": 50,
        "pqr_quota": 50,
        "ppqr_quota": 50
    },
    "personal_flagship": {
        "name": "个人旗舰版",
        "price": "¥99/月",
        "wps_quota": 100,
        "pqr_quota": 100,
        "ppqr_quota": 100
    }
}

# 企业会员等级配置
ENTERPRISE_TIERS = {
    "enterprise": {
        "name": "企业版",
        "price": "¥199/月",
        "wps_quota": 200,
        "pqr_quota": 200,
        "ppqr_quota": 200,
        "max_employees": 10  # 多工厂数量（员工数）
    },
    "enterprise_pro": {
        "name": "企业版PRO",
        "price": "¥399/月",
        "wps_quota": 400,
        "pqr_quota": 400,
        "ppqr_quota": 400,
        "max_employees": 20
    },
    "enterprise_pro_max": {
        "name": "企业版PRO MAX",
        "price": "¥899/月",
        "wps_quota": 500,
        "pqr_quota": 500,
        "ppqr_quota": 500,
        "max_employees": 50
    }
}
```

### 数据模型默认值

```python
# 用户表
class User(Base):
    membership_tier = Column(String(50), default="free")  # 默认免费版

# 企业表
class Company(Base):
    membership_tier = Column(String(50), default="enterprise")  # 默认企业版
```

---

## 📝 已更新的文档

以下文档已全部更新为正确的会员等级配置：

1. ✅ `MEMBERSHIP_AND_QUOTA_SYSTEM.md`
   - 会员等级表格
   - 代码配置示例
   - 数据模型默认值

2. ✅ `DATA_ISOLATION_AND_PERMISSION_ARCHITECTURE.md`
   - 会员体系架构
   - 会员等级配置代码
   - 会员权益对比表

3. ✅ `COMPLETE_ARCHITECTURE_SUMMARY.md`
   - 会员配额系统概述

---

## ⚠️ 重要注意事项

### 1. 免费版不支持pPQR

```python
# 创建pPQR时需要检查
if user.membership_tier == "free":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="免费版不支持pPQR功能，请升级会员"
    )
```

### 2. 配额检查逻辑

```python
def check_quota(self, user, workspace_context, quota_type, increment):
    # 获取配额限制
    quota_limit = tier_config.get(f"{quota_type}_quota", 0)
    
    # 如果配额为0，表示不支持该功能
    if quota_limit == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您的会员等级不支持{quota_type}功能，请升级会员"
        )
    
    # 检查是否超出限制
    if current_usage + increment > quota_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"配额不足：您的配额已用完（{current_usage}/{quota_limit}），请升级会员"
        )
```

### 3. 企业员工数量限制

```python
# 添加员工时检查
def add_employee(self, company_id, user_id):
    company = self.db.query(Company).filter(Company.id == company_id).first()
    
    # 获取当前员工数
    current_employees = self.db.query(CompanyEmployee).filter(
        CompanyEmployee.company_id == company_id,
        CompanyEmployee.status == "active"
    ).count()
    
    # 获取会员等级配置
    tier = company.membership_tier or "enterprise"
    tier_config = ENTERPRISE_TIERS.get(tier, ENTERPRISE_TIERS["enterprise"])
    max_employees = tier_config.get("max_employees", 10)
    
    # 检查是否超出限制
    if current_employees >= max_employees:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"员工数量已达上限（{current_employees}/{max_employees}），请升级会员"
        )
```

---

## 🎯 总结

### 主要变更

1. **个人会员**：
   - ❌ 删除：`basic`（基础版）、`pro`（专业版）、`unlimited`（无限版）
   - ✅ 新增：`personal_pro`（专业版）、`personal_advanced`（高级版）、`personal_flagship`（旗舰版）
   - ✅ 免费版不支持pPQR功能

2. **企业会员**：
   - ❌ 删除：`enterprise_basic`（企业基础版）、`enterprise_unlimited`（企业无限版）
   - ✅ 修改：基础等级从`enterprise_basic`改为`enterprise`
   - ✅ 新增：`max_employees`字段（多工厂数量限制）

3. **配额配置**：
   - ✅ 个人专业版及以上等级的WPS、PQR、pPQR配额完全相同
   - ✅ 免费版pPQR配额为0（不支持）
   - ✅ 企业版增加员工数量限制

### 影响范围

- ✅ 所有架构文档已更新
- ⚠️ 需要更新后端配置文件（`backend/app/core/config.py`）
- ⚠️ 需要更新前端配置文件（`frontend/src/config/membership.ts`）
- ⚠️ 需要更新数据库默认值（如果已有数据，需要迁移）

---

**所有文档已更新为正确的会员等级配置！** ✅

