/**
 * 焊工记录服务（工作履历、工作记录、培训记录、考核记录）
 */
import api from './api';

// ==================== 类型定义 ====================

export interface WelderWorkHistory {
  id: number;
  welder_id: number;
  company_name: string;
  position: string;
  start_date: string;
  end_date?: string;
  department?: string;
  location?: string;
  job_description?: string;
  achievements?: string;
  leaving_reason?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface WelderWorkRecord {
  id: number;
  welder_id: number;
  work_date: string;
  work_shift?: string;
  work_hours?: number;
  welding_process?: string;
  welding_position?: string;
  base_material?: string;
  filler_material?: string;
  weld_length?: number;
  weld_weight?: number;
  quality_result?: string;
  defect_count?: number;
  rework_count?: number;
  production_task_id?: number;
  wps_id?: number;
  notes?: string;
  created_by: number;
  created_at: string;
}

export interface WelderTrainingRecord {
  id: number;
  welder_id: number;
  training_code?: string;
  training_name: string;
  training_type?: string;
  training_category?: string;
  start_date: string;
  end_date?: string;
  duration_hours?: number;
  training_organization?: string;
  trainer_name?: string;
  training_location?: string;
  training_content?: string;
  training_objectives?: string;
  training_materials?: string;
  assessment_method?: string;
  assessment_score?: number;
  assessment_result?: string;
  pass_status?: boolean;
  certificate_issued?: boolean;
  certificate_number?: string;
  certificate_file_url?: string;
  notes?: string;
  attachments?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface WelderAssessmentRecord {
  id: number;
  welder_id: number;
  assessment_code?: string;
  assessment_name: string;
  assessment_type?: string;
  assessment_category?: string;
  assessment_date: string;
  duration_minutes?: number;
  assessment_content?: string;
  assessment_standards?: string;
  assessment_items?: string;
  assessor_name?: string;
  assessor_organization?: string;
  assessment_location?: string;
  theory_score?: number;
  practical_score?: number;
  total_score?: number;
  pass_score?: number;
  assessment_result?: string;
  pass_status?: boolean;
  grade_level?: string;
  certificate_issued?: boolean;
  certificate_number?: string;
  certificate_file_url?: string;
  notes?: string;
  attachments?: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

// ==================== 工作履历服务 ====================

export const workHistoryService = {
  /**
   * 获取工作履历列表
   */
  async getList(welderId: number, params?: any) {
    const response = await api.get(`/welders/${welderId}/work-histories`, { params });
    return response.data.data || response.data;
  },

  /**
   * 添加工作履历
   */
  async create(welderId: number, data: Partial<WelderWorkHistory>, params?: any) {
    const response = await api.post(`/welders/${welderId}/work-histories`, data, { params });
    return response.data.data || response.data;
  },

  /**
   * 删除工作履历
   */
  async delete(welderId: number, historyId: number, params?: any) {
    const response = await api.delete(`/welders/${welderId}/work-histories/${historyId}`, { params });
    return response.data;
  },
};

// ==================== 工作记录服务 ====================

export const workRecordService = {
  /**
   * 获取工作记录列表
   */
  async getList(welderId: number, params?: any) {
    const response = await api.get(`/welders/${welderId}/work-records`, { params });
    return response.data.data || response.data;
  },

  /**
   * 添加工作记录
   */
  async create(welderId: number, data: Partial<WelderWorkRecord>, params?: any) {
    const response = await api.post(`/welders/${welderId}/work-records`, data, { params });
    return response.data.data || response.data;
  },

  /**
   * 删除工作记录
   */
  async delete(welderId: number, recordId: number, params?: any) {
    const response = await api.delete(`/welders/${welderId}/work-records/${recordId}`, { params });
    return response.data;
  },
};

// ==================== 培训记录服务 ====================

export const trainingRecordService = {
  /**
   * 获取培训记录列表
   */
  async getList(welderId: number, params?: any) {
    const response = await api.get(`/welders/${welderId}/training-records`, { params });
    return response.data.data || response.data;
  },

  /**
   * 添加培训记录
   */
  async create(welderId: number, data: Partial<WelderTrainingRecord>, params?: any) {
    const response = await api.post(`/welders/${welderId}/training-records`, data, { params });
    return response.data.data || response.data;
  },

  /**
   * 删除培训记录
   */
  async delete(welderId: number, recordId: number, params?: any) {
    const response = await api.delete(`/welders/${welderId}/training-records/${recordId}`, { params });
    return response.data;
  },
};

// ==================== 考核记录服务 ====================

export const assessmentRecordService = {
  /**
   * 获取考核记录列表
   */
  async getList(welderId: number, params?: any) {
    const response = await api.get(`/welders/${welderId}/assessment-records`, { params });
    return response.data.data || response.data;
  },

  /**
   * 添加考核记录
   */
  async create(welderId: number, data: Partial<WelderAssessmentRecord>, params?: any) {
    const response = await api.post(`/welders/${welderId}/assessment-records`, data, { params });
    return response.data.data || response.data;
  },

  /**
   * 删除考核记录
   */
  async delete(welderId: number, recordId: number, params?: any) {
    const response = await api.delete(`/welders/${welderId}/assessment-records/${recordId}`, { params });
    return response.data;
  },
};

