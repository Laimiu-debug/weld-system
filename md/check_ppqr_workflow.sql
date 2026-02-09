-- 检查pPQR审批工作流配置

-- 查询pPQR的审批工作流
SELECT 
    id,
    name,
    document_type,
    company_id,
    is_active,
    created_at
FROM approval_workflow_definitions
WHERE document_type = 'ppqr';

-- 查询所有审批工作流
SELECT 
    id,
    name,
    document_type,
    company_id,
    is_active
FROM approval_workflow_definitions
ORDER BY document_type, id;

