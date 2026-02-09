-- 为PQR和pPQR创建审批工作流
-- 请根据实际的company_id修改

-- 1. 为PQR创建审批工作流
INSERT INTO approval_workflow_definitions (
    name,
    description,
    document_type,
    company_id,
    steps,
    is_active,
    created_at,
    updated_at
) VALUES (
    'PQR标准审批流程',
    'PQR文档的标准审批流程',
    'pqr',
    1,  -- 请修改为实际的company_id，如果是个人工作区则设为NULL
    '[
        {
            "step_name": "技术审核",
            "approver_type": "role",
            "approver_ids": [2],
            "approval_mode": "any",
            "time_limit_hours": 48
        },
        {
            "step_name": "质量审批",
            "approver_type": "role",
            "approver_ids": [3],
            "approval_mode": "any",
            "time_limit_hours": 24
        }
    ]'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 2. 为pPQR创建审批工作流
INSERT INTO approval_workflow_definitions (
    name,
    description,
    document_type,
    company_id,
    steps,
    is_active,
    created_at,
    updated_at
) VALUES (
    'pPQR标准审批流程',
    'pPQR文档的标准审批流程',
    'ppqr',
    1,  -- 请修改为实际的company_id，如果是个人工作区则设为NULL
    '[
        {
            "step_name": "技术审核",
            "approver_type": "role",
            "approver_ids": [2],
            "approval_mode": "any",
            "time_limit_hours": 48
        }
    ]'::jsonb,
    true,
    NOW(),
    NOW()
);

-- 查看创建的工作流
SELECT id, name, document_type, company_id, is_active 
FROM approval_workflow_definitions 
WHERE document_type IN ('pqr', 'ppqr');

