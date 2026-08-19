/**
 * Production Management API Service
 * 生产管理API服务
 */
import axios from 'axios';
import { message } from 'antd';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ==================== 类型定义 ====================

export interface ProductionTask {
  id: number;
  task_number: string;
  task_name: string;
  task_type?: string;
  
  // 关联信息
  wps_id?: number;
  pqr_id?: number;
  project_id?: number;
  customer_id?: number;
  
  // 任务详情
  description?: string;
  technical_requirements?: string;
  quality_standards?: string;
  
  // 计划信息
  planned_start_date?: string;
  planned_end_date?: string;
  planned_duration_hours?: number;
  
  // 实际信息
  actual_start_date?: string;
  actual_end_date?: string;
  actual_duration_hours?: number;
  
  // 人员分配
  assigned_welder_id?: number;
  assigned_equipment_id?: number;
  assigned_inspector_id?: number;
  assigned_supervisor_id?: number;
  team_members?: string;
  wps_number?: string;
  wps_title?: string;
  welder_name?: string;
  welder_code?: string;
  equipment_name?: string;
  equipment_code?: string;
  
  // 状态信息
  status: string;
  priority: string;
  progress_percentage: number;
  notes?: string;
  
  // 数据隔离字段
  workspace_type: string;
  user_id: number;
  company_id?: number;
  factory_id?: number;
  access_level: string;
  
  // 审计字段
  created_by: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ProductionTaskCreate {
  task_number: string;
  task_name: string;
  task_type?: string;
  wps_id?: number;
  pqr_id?: number;
  description?: string;
  technical_requirements?: string;
  quality_standards?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  planned_duration_hours?: number;
  assigned_welder_id?: number;
  assigned_equipment_id?: number;
  assigned_inspector_id?: number;
  assigned_supervisor_id?: number;
  status?: string;
  priority?: string;
  project_name?: string;
  base_material?: string;
  weld_length_planned?: number;
  safety_requirements?: string;
  quality_requirements?: string;
  work_description?: string;
}

export interface ProductionTaskUpdate {
  task_name?: string;
  task_type?: string;
  description?: string;
  technical_requirements?: string;
  quality_standards?: string;
  planned_start_date?: string;
  planned_end_date?: string;
  planned_duration_hours?: number;
  actual_start_date?: string;
  actual_end_date?: string;
  actual_duration_hours?: number;
  assigned_welder_id?: number;
  assigned_equipment_id?: number;
  assigned_inspector_id?: number;
  assigned_supervisor_id?: number;
  status?: string;
  priority?: string;
  progress_percentage?: number;
  wps_id?: number;
}

export interface ProductionTaskListParams {
  workspace_type: string;
  company_id?: number;
  factory_id?: number;
  skip?: number;
  limit?: number;
  search?: string;
  status?: string;
  priority?: string;
  assigned_welder_id?: number;
}

export interface ProductionTaskListResponse {
  success: boolean;
  data: {
    items: ProductionTask[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
  message: string;
}

// ==================== API函数 ====================

/**
 * 获取生产任务列表
 */
export const getProductionTasks = async (
  params: ProductionTaskListParams
): Promise<ProductionTaskListResponse> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_BASE_URL}/production/tasks`, {
      params,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || '获取生产任务列表失败';
    message.error(errorMessage);
    throw error;
  }
};

/**
 * 创建生产任务
 */
export const createProductionTask = async (
  data: ProductionTaskCreate,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: ProductionTask; message: string }> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post(
      `${API_BASE_URL}/production/tasks`,
      data,
      {
        params: {
          workspace_type: workspaceType,
          company_id: companyId,
          factory_id: factoryId,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    message.success('生产任务创建成功');
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || '创建生产任务失败';
    message.error(errorMessage);
    throw error;
  }
};

/**
 * 获取生产任务详情
 */
export const getProductionTaskById = async (
  id: number,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: ProductionTask; message: string }> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(
      `${API_BASE_URL}/production/tasks/${id}`,
      {
        params: {
          workspace_type: workspaceType,
          company_id: companyId,
          factory_id: factoryId,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || '获取生产任务详情失败';
    message.error(errorMessage);
    throw error;
  }
};

/**
 * 更新生产任务
 */
export const updateProductionTask = async (
  id: number,
  data: ProductionTaskUpdate,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: ProductionTask; message: string }> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.put(
      `${API_BASE_URL}/production/tasks/${id}`,
      data,
      {
        params: {
          workspace_type: workspaceType,
          company_id: companyId,
          factory_id: factoryId,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    message.success('生产任务更新成功');
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || '更新生产任务失败';
    message.error(errorMessage);
    throw error;
  }
};

/**
 * 删除生产任务
 */
export const deleteProductionTask = async (
  id: number,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; message: string }> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.delete(
      `${API_BASE_URL}/production/tasks/${id}`,
      {
        params: {
          workspace_type: workspaceType,
          company_id: companyId,
          factory_id: factoryId,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    message.success('生产任务删除成功');
    return response.data;
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || '删除生产任务失败';
    message.error(errorMessage);
    throw error;
  }
};

/**
 * 更新生产任务进度
 */
export const updateProductionTaskProgress = async (
  id: number,
  progressPercentage: number,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: ProductionTask; message: string }> => {
  return updateProductionTask(
    id,
    { progress_percentage: progressPercentage },
    workspaceType,
    companyId,
    factoryId
  );
};

/**
 * 更新生产任务状态
 */
export const updateProductionTaskStatus = async (
  id: number,
  status: string,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: ProductionTask; message: string }> => {
  return updateProductionTask(
    id,
    { status },
    workspaceType,
    companyId,
    factoryId
  );
};

export interface ProductionRecord {
  id: number;
  task_id: number;
  record_number?: string;
  record_date: string;
  work_shift?: string;
  start_time?: string;
  end_time?: string;
  duration_hours?: number;
  work_description?: string;
  quantity_completed?: number;
  weld_length?: number;
  notes?: string;
}

export interface ProductionStatistics {
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  total_weld_length: number;
  total_work_hours: number;
  average_progress: number;
}

const workspaceParams = (
  workspaceType: string,
  companyId?: number,
  factoryId?: number
) => ({
  workspace_type: workspaceType,
  company_id: companyId,
  factory_id: factoryId,
});

export const getProductionRecords = async (
  taskId: number,
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: { items: ProductionRecord[]; total: number } }> => {
  const token = localStorage.getItem('token');
  const response = await axios.get(`${API_BASE_URL}/production/tasks/${taskId}/records`, {
    params: workspaceParams(workspaceType, companyId, factoryId),
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const createProductionRecord = async (
  taskId: number,
  data: Partial<ProductionRecord> & { record_date: string },
  workspaceType: string,
  companyId?: number,
  factoryId?: number
) => {
  const token = localStorage.getItem('token');
  const response = await axios.post(
    `${API_BASE_URL}/production/tasks/${taskId}/records`,
    data,
    {
      params: workspaceParams(workspaceType, companyId, factoryId),
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  message.success('生产记录已保存');
  return response.data;
};

export const getProductionStatistics = async (
  workspaceType: string,
  companyId?: number,
  factoryId?: number
): Promise<{ success: boolean; data: ProductionStatistics }> => {
  const token = localStorage.getItem('token');
  const response = await axios.get(`${API_BASE_URL}/production/statistics/overview`, {
    params: workspaceParams(workspaceType, companyId, factoryId),
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export default {
  getProductionTasks,
  createProductionTask,
  getProductionTaskById,
  updateProductionTask,
  deleteProductionTask,
  updateProductionTaskProgress,
  updateProductionTaskStatus,
  getProductionRecords,
  createProductionRecord,
  getProductionStatistics,
};

