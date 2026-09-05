from pathlib import Path
import subprocess
paths = '''backend/app/api/v1/endpoints/business_mvp.py
backend/app/models/business_extensions.py
backend/app/models/production.py
backend/app/models/quality.py
backend/app/schemas/production.py
backend/app/schemas/quality.py
backend/app/services/invitation_service.py
backend/app/services/production_service.py
backend/app/services/quality_service.py
backend/app/services/welder_career_mixin.py
backend/app/services/workspace_entity_service.py
frontend/src/App.tsx
frontend/src/components/Welders/WorkHistory/WorkHistoryList.tsx
frontend/src/components/Welders/WorkHistory/WorkHistoryModal.tsx
frontend/src/hooks/useEnterprise.ts
frontend/src/pages/Employees/EmployeeManagement.tsx
frontend/src/pages/Employees/PerformanceManagement.tsx
frontend/src/pages/Enterprise/Employees.tsx
frontend/src/pages/Enterprise/Invitations.tsx
frontend/src/pages/Production/ProductionPlanManagement.tsx
frontend/src/pages/Quality/QualityCreate.tsx
frontend/src/pages/Quality/QualityDetail.tsx
frontend/src/pages/Quality/QualityEdit.tsx
frontend/src/pages/Quality/QualityStandardManagement.tsx
frontend/src/pages/Reports/CustomReportBuilder.tsx
frontend/src/services/businessExtensions.ts
frontend/src/services/quality.ts
frontend/src/services/welderRecords.ts'''.splitlines()
for name in paths:
    original=subprocess.check_output(['git','show','HEAD:'+name])
    newline='\r\n' if original.count(b'\r\n') > original.count(b'\n')/2 else '\n'
    path=Path(name)
    text=path.read_text(encoding='utf-8')
    path.write_bytes(text.replace('\n',newline).encode('utf-8'))
print('Preserved HEAD line ending styles for',len(paths),'modified files')
