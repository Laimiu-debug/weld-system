# Quota System Quick Reference Guide

## Module Categories

### Physical Asset Modules (No Quota in Personal Workspaces)
- 🔧 **Equipment** (设备) - `QuotaType.EQUIPMENT`
- 🧪 **Materials** (焊材) - `QuotaType.MATERIALS`
- 👷 **Welders** (焊工) - `QuotaType.WELDERS`
- 🏭 **Production** (生产) - `QuotaType.PRODUCTION`
- ✅ **Quality** (质量) - `QuotaType.QUALITY`

**Rationale**: Individual users typically don't have large quantities of physical assets.

### Document Modules (Quota in All Workspaces)
- 📄 **WPS** (Welding Procedure Specifications) - `QuotaType.WPS`
- 📋 **PQR** (Procedure Qualification Records) - `QuotaType.PQR`
- 📝 **pPQR** (Preliminary PQR) - `QuotaType.PPQR`

**Rationale**: Even individual users may accumulate many documents over time.

## Quota Behavior Matrix

| Module Type | Personal Workspace | Enterprise Workspace |
|-------------|-------------------|---------------------|
| Equipment | ✅ No Quota Check | ⚠️ Check Quota |
| Materials | ✅ No Quota Check | ⚠️ Check Quota |
| Welders | ✅ No Quota Check | ⚠️ Check Quota |
| Production | ✅ No Quota Check | ⚠️ Check Quota |
| Quality | ✅ No Quota Check | ⚠️ Check Quota |
| WPS | ⚠️ Check Quota | ⚠️ Check Quota |
| PQR | ⚠️ Check Quota | ⚠️ Check Quota |
| pPQR | ⚠️ Check Quota | ⚠️ Check Quota |
| Storage | ⚠️ Check Quota | ⚠️ Check Quota |

## How to Use in Your Service

### Step 1: Import QuotaService
```python
from app.services.quota_service import QuotaService, QuotaType
```

### Step 2: Initialize in Your Service
```python
class YourService:
    def __init__(self, db: Session):
        self.db = db
        self.quota_service = QuotaService(db)
```

### Step 3: Check Quota Before Creating Resource
```python
def create_resource(self, current_user, data, workspace_context):
    # Check quota (automatically skips for physical assets in personal workspace)
    self.quota_service.check_quota(
        current_user, 
        workspace_context, 
        QuotaType.EQUIPMENT,  # or MATERIALS, WELDERS, etc.
        1  # increment amount
    )
    
    # Create your resource
    resource = YourModel(**data)
    self.db.add(resource)
    self.db.commit()
    
    # Update quota usage (automatically skips for physical assets in personal workspace)
    self.quota_service.increment_quota_usage(
        current_user,
        workspace_context,
        QuotaType.EQUIPMENT,
        1
    )
    
    return resource
```

### Step 4: Update Quota When Deleting Resource
```python
def delete_resource(self, resource_id, current_user, workspace_context):
    # Delete your resource
    resource = self.get_resource(resource_id)
    resource.is_active = False
    self.db.commit()
    
    # Decrement quota usage (automatically skips for physical assets in personal workspace)
    self.quota_service.decrement_quota_usage(
        current_user,
        workspace_context,
        QuotaType.EQUIPMENT,
        1
    )
    
    return True
```

## Available Quota Types

```python
# Document modules (always checked)
QuotaType.WPS
QuotaType.PQR
QuotaType.PPQR

# Physical asset modules (skipped in personal workspace)
QuotaType.EQUIPMENT
QuotaType.MATERIALS
QuotaType.WELDERS
QuotaType.PRODUCTION
QuotaType.QUALITY

# Other quota types
QuotaType.STORAGE
QuotaType.EMPLOYEES
QuotaType.FACTORIES
```

## Error Handling

### Quota Exceeded Error
```python
try:
    self.quota_service.check_quota(user, workspace_context, quota_type, 1)
except HTTPException as e:
    # e.status_code == 403
    # e.detail == "个人工作区equipment配额不足。已使用: X/Y"
    # or
    # e.detail == "企业equipment配额不足。已使用: X/Y"
    pass
```

### Invalid Quota Type Error
```python
try:
    self.quota_service.check_quota(user, workspace_context, "invalid_type", 1)
except ValueError as e:
    # e.args[0] == "不支持的配额类型: invalid_type"
    pass
```

## Workspace Context

### Creating Workspace Context
```python
from app.core.data_access import WorkspaceContext

# Personal workspace
workspace_context = WorkspaceContext(
    user_id=current_user.id,
    workspace_type="personal",
    company_id=None,
    factory_id=None
)

# Enterprise workspace
workspace_context = WorkspaceContext(
    user_id=current_user.id,
    workspace_type="enterprise",
    company_id=company_id,
    factory_id=factory_id
)
```

### Checking Workspace Type
```python
if workspace_context.is_personal():
    # Personal workspace logic
    pass

if workspace_context.is_enterprise():
    # Enterprise workspace logic
    pass
```

## Frontend Integration

### Accessing Current Membership Info
```typescript
import { useMembership } from '@/contexts/MembershipContext'

function YourComponent() {
  const { membershipInfo, refreshMembership } = useMembership()
  
  // Access current tier
  console.log(membershipInfo?.tier)
  
  // Access quotas
  console.log(membershipInfo?.quotas)
  
  // Refresh membership info
  await refreshMembership()
}
```

### Triggering Workspace Switch
```typescript
import { triggerWorkspaceSwitch } from '@/contexts/MembershipContext'

// After switching workspace
triggerWorkspaceSwitch(newWorkspace, user.membership_type)
```

## Testing Checklist

### Backend Tests
- [ ] Create equipment in personal workspace (should succeed)
- [ ] Create equipment in enterprise workspace with quota available (should succeed)
- [ ] Create equipment in enterprise workspace with quota exceeded (should fail with 403)
- [ ] Create WPS in personal workspace with quota available (should succeed)
- [ ] Create WPS in personal workspace with quota exceeded (should fail with 403)
- [ ] Delete equipment and verify quota decrements (enterprise only)
- [ ] Delete WPS and verify quota decrements (all workspaces)

### Frontend Tests
- [ ] Switch from personal to enterprise workspace
- [ ] Verify membership tier updates in header
- [ ] Verify quota display updates
- [ ] Switch from enterprise to personal workspace
- [ ] Verify membership tier updates
- [ ] Create equipment in personal workspace (no quota warning)
- [ ] Create WPS in personal workspace (shows quota usage)

## Common Pitfalls

### ❌ Don't: Manually check workspace type before calling quota service
```python
# Bad - duplicates logic
if workspace_context.is_personal():
    # Skip quota check
    pass
else:
    self.quota_service.check_quota(...)
```

### ✅ Do: Let quota service handle the logic
```python
# Good - quota service handles all logic
self.quota_service.check_quota(user, workspace_context, quota_type, 1)
```

### ❌ Don't: Forget to update quota usage after creation
```python
# Bad - quota not tracked
resource = create_resource()
self.db.commit()
# Missing: self.quota_service.increment_quota_usage(...)
```

### ✅ Do: Always update quota after successful creation
```python
# Good - quota properly tracked
resource = create_resource()
self.db.commit()
self.quota_service.increment_quota_usage(user, workspace_context, quota_type, 1)
```

## Support

For questions or issues:
1. Check `QUOTA_CHECK_CHANGES_SUMMARY.md` for detailed implementation
2. Review `backend/app/services/quota_service.py` for source code
3. Check existing implementations in `backend/app/services/equipment_service.py`

