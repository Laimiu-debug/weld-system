/**
 * 审批系统API服务
 */
import api from './api';

export interface SubmitApprovalRequest {
  document_type: string;
  document_ids: number[];
  notes?: string;
}

export interface ApprovalActionRequest {
  action?: 'approve' | 'reject' | 'return';
  comment: string;
  attachments?: string[];
}

export interface BatchApprovalRequest {
  instance_ids: number[];
  comment: string;
}

export interface ApprovalWorkflowStep {
  step_number?: number;
  description?: string;
  step_name: string;
  approver_type: 'role' | 'user' | 'department';
  approver_id: number;
  approval_mode: 'any' | 'all' | 'sequential';
  time_limit_hours?: number;
}

export interface ApprovalWorkflowDefinition {
  id: number;
  name: string;
  code: string;
  document_type: string;
  description?: string;
  steps: ApprovalWorkflowStep[];
  is_active: boolean;
  is_default: boolean;
  company_id?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkflowData {
  name: string;
  code: string;
  document_type: string;
  description?: string;
  steps: ApprovalWorkflowStep[];
  is_active?: boolean;
}

export interface ApprovalInstance {
  id: number;
  workflow_id: number;
  document_type: string;
  document_id: number;
  document_number: string;
  document_title: string;
  status: string;
  current_step: number;
  current_step_name: string;
  submitter_id: number;
  submitted_at: string;
  completed_at?: string;
  priority: string;
  notes?: string;
}

export interface ApprovalHistory {
  id: number;
  instance_id: number;
  step_number: number;
  step_name: string;
  action: string;
  operator_id: number;
  operator_name: string;
  comment: string;
  result?: string;
  created_at: string;
  attachments?: string[];
}

export interface ApprovalStatistics {
  total_pending: number;
  total_approved: number;
  total_rejected: number;
  my_pending: number;
  my_submitted: number;
  overdue: number;
}

export const approvalApi = {
  /**
   * 提交审批
   */
  submitForApproval: (data: SubmitApprovalRequest) => {
    return api.post('/approvals/submit', data);
  },

  /**
   * 批准文档
   */
  approve: (instanceId: number, data: ApprovalActionRequest) => {
    return api.post(`/approvals/${instanceId}/approve`, data);
  },

  /**
   * 拒绝文档
   */
  reject: (instanceId: number, data: ApprovalActionRequest) => {
    return api.post(`/approvals/${instanceId}/reject`, data);
  },

  /**
   * 退回文档
   */
  return: (instanceId: number, data: ApprovalActionRequest) => {
    return api.post(`/approvals/${instanceId}/return`, data);
  },

  /**
   * 取消审批
   */
  cancel: (instanceId: number, comment: string) => {
    return api.post(`/approvals/${instanceId}/cancel`, null, {
      params: { comment },
    });
  },

  /**
   * 批量批准
   */
  batchApprove: (data: BatchApprovalRequest) => {
    return api.post('/approvals/batch/approve', data);
  },

  /**
   * 批量拒绝
   */
  batchReject: (data: BatchApprovalRequest) => {
    return api.post('/approvals/batch/reject', data);
  },

  /**
   * 获取待我审批的列表
   */
  getPendingApprovals: (params: {
    workspace_type: string;
    workspace_id?: string;
    page?: number;
    page_size?: number;
  }) => {
    return api.get<{
      items: ApprovalInstance[];
      total: number;
      page: number;
      page_size: number;
    }>('/approvals/pending', { params });
  },

  /**
   * 获取我提交的审批列表
   */
  getMySubmissions: (params: {
    workspace_type: string;
    workspace_id?: string;
    status_filter?: string;
    page?: number;
    page_size?: number;
  }) => {
    return api.get<{
      items: ApprovalInstance[];
      total: number;
      page: number;
      page_size: number;
    }>('/approvals/my-submissions', { params });
  },

  /**
   * 获取审批历史
   */
  getHistory: (instanceId: number) => {
    return api.get<ApprovalHistory[]>(`/approvals/${instanceId}/history`);
  },

  /**
   * 获取审批统计
   */
  getStatistics: (params: {
    workspace_type: string;
    workspace_id?: string;
  }) => {
    return api.get<ApprovalStatistics>('/approvals/statistics', { params });
  },

  /**
   * 获取审批详情
   */
  getDetail: (instanceId: number) => {
    return api.get<{
      instance: ApprovalInstance;
      history: ApprovalHistory[];
      permissions: {
        can_approve: boolean;
        can_cancel: boolean;
      };
    }>(`/approvals/${instanceId}`);
  },

  /**
   * 获取工作流列表
   */
  getWorkflows: (params?: {
    document_type?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }) => {
    return api.get<{
      items: ApprovalWorkflowDefinition[];
      total: number;
      page: number;
      page_size: number;
    }>('/approvals/workflows', { params });
  },

  /**
   * 获取工作流详情
   */
  getWorkflow: (workflowId: number) => {
    return api.get<ApprovalWorkflowDefinition>(`/approvals/workflows/${workflowId}`);
  },

  /**
   * 创建工作流
   */
  createWorkflow: (data: CreateWorkflowData) => {
    return api.post<ApprovalWorkflowDefinition>('/approvals/workflows', data);
  },

  /**
   * 更新工作流
   */
  updateWorkflow: (workflowId: number, data: Partial<CreateWorkflowData>) => {
    return api.put<ApprovalWorkflowDefinition>(`/approvals/workflows/${workflowId}`, data);
  },

  /**
   * 删除工作流
   */
  deleteWorkflow: (workflowId: number) => {
    return api.delete(`/approvals/workflows/${workflowId}`);
  },

  /**
   * 切换工作流状态
   */
  toggleWorkflowStatus: (workflowId: number, isActive: boolean) => {
    return api.patch(`/approvals/workflows/${workflowId}/toggle?is_active=${isActive}`);
  },

  /**
   * 设置为默认工作流
   */
  setDefaultWorkflow: (workflowId: number) => {
    return api.patch(`/approvals/workflows/${workflowId}/set-default`);
  },
};

export default approvalApi;

