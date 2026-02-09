/**
 * 焊工证书管理服务
 */
import api from './api';

// ==================== 类型定义 ====================

/**
 * 合格项目条目
 */
export interface QualifiedItem {
  item: string;          // 完整代号，如：GTAW-FeIV-6G-3/159-FefS-02/10/12
  description?: string;  // 描述，如：氩弧焊-碳钢-全位置
  notes?: string;        // 备注
}

/**
 * 合格范围条目
 */
export interface QualifiedRangeItem {
  name: string;   // 项目名称，如：母材、焊接位置、厚度范围等
  value: string;  // 范围值，如：Q345R、1G,2G,3G、3-12mm等
  notes?: string; // 备注
}

/**
 * 附件信息
 */
export interface AttachmentItem {
  name: string;  // 文件名
  url: string;   // 文件URL
  type: string;  // 文件类型：pdf, image, etc.
  size?: number; // 文件大小（字节）
}

/**
 * 证书类型
 */
export interface WelderCertification {
  id: number;
  welder_id: number;
  user_id: number;
  company_id?: number;
  
  // 证书基本信息
  certification_number: string;
  certification_type: string;
  certification_level?: string;
  certification_standard?: string;
  certification_system?: string;
  project_name?: string;
  
  // 颁发信息
  issuing_authority: string;
  issuing_country?: string;
  issue_date: string;
  expiry_date?: string;
  
  // 合格项目 - JSON格式
  qualified_items?: string;  // JSON字符串，解析后为 QualifiedItem[]

  // 合格范围 - JSON格式
  qualified_range?: string;  // JSON字符串，解析后为 QualifiedRangeItem[]
  
  // 考试信息
  exam_date?: string;
  exam_location?: string;
  exam_score?: number;
  practical_test_result?: string;
  theory_test_result?: string;
  
  // 复审信息
  renewal_date?: string;
  renewal_count?: number;
  next_renewal_date?: string;
  renewal_result?: string;
  renewal_notes?: string;
  
  // 状态和附件
  status: string;
  is_primary: boolean;
  certificate_file_url?: string;
  attachments?: string;
  notes?: string;
  
  // 审计字段
  created_by: number;
  updated_by?: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

/**
 * 创建证书请求
 */
export interface CreateCertificationRequest {
  certification_number: string;
  certification_type: string;
  certification_level?: string;
  certification_standard?: string;
  certification_system?: string;
  project_name?: string;

  issuing_authority: string;
  issuing_country?: string;
  issue_date: string;
  expiry_date?: string;

  qualified_items?: string;  // JSON字符串
  qualified_range?: string;  // JSON字符串

  exam_date?: string;
  exam_location?: string;
  exam_score?: number;
  practical_test_result?: string;
  theory_test_result?: string;

  renewal_date?: string;
  renewal_count?: number;
  next_renewal_date?: string;
  renewal_result?: string;
  renewal_notes?: string;

  status?: string;
  is_primary?: boolean;
  certificate_file_url?: string;
  attachments?: string;  // JSON字符串
  notes?: string;
}

/**
 * 更新证书请求
 */
export type UpdateCertificationRequest = Partial<CreateCertificationRequest>;

/**
 * 证书列表响应
 */
export interface CertificationListResponse {
  items: WelderCertification[];
  total: number;
}

// ==================== 服务方法 ====================

/**
 * 证书服务类
 */
class CertificationService {
  /**
   * 获取焊工证书列表
   */
  async getList(
    welderId: number,
    workspaceType: string,
    companyId?: number,
    factoryId?: number
  ): Promise<CertificationListResponse> {
    const params: any = {
      workspace_type: workspaceType,
    };

    if (companyId) params.company_id = companyId;
    if (factoryId) params.factory_id = factoryId;

    const response = await api.get(`/welders/${welderId}/certifications`, { params });
    // 后端返回 { success: true, data: { items: [], total: 0 }, message: "..." }
    // API 拦截器会将其包装为 { success: true, data: { success: true, data: { items: [], total: 0 } } }
    // 所以我们需要访问 response.data.data
    return response.data.data || response.data;
  }

  /**
   * 创建证书
   */
  async create(
    welderId: number,
    data: CreateCertificationRequest,
    workspaceType: string,
    companyId?: number,
    factoryId?: number
  ): Promise<WelderCertification> {
    const params: any = {
      workspace_type: workspaceType,
    };

    if (companyId) params.company_id = companyId;
    if (factoryId) params.factory_id = factoryId;

    const response = await api.post(`/welders/${welderId}/certifications`, data, { params });
    return response.data.data || response.data;
  }

  /**
   * 更新证书
   */
  async update(
    welderId: number,
    certificationId: number,
    data: UpdateCertificationRequest,
    workspaceType: string,
    companyId?: number,
    factoryId?: number
  ): Promise<WelderCertification> {
    const params: any = {
      workspace_type: workspaceType,
    };

    if (companyId) params.company_id = companyId;
    if (factoryId) params.factory_id = factoryId;

    const response = await api.put(
      `/welders/${welderId}/certifications/${certificationId}`,
      data,
      { params }
    );
    return response.data.data || response.data;
  }

  /**
   * 删除证书
   */
  async delete(
    welderId: number,
    certificationId: number,
    workspaceType: string,
    companyId?: number,
    factoryId?: number
  ): Promise<void> {
    const params: any = {
      workspace_type: workspaceType,
    };
    
    if (companyId) params.company_id = companyId;
    if (factoryId) params.factory_id = factoryId;
    
    await api.delete(`/welders/${welderId}/certifications/${certificationId}`, { params });
  }

  /**
   * 上传证书附件
   */
  async uploadAttachment(
    welderId: number,
    certificationId: number,
    file: File,
    workspaceType: string,
    companyId?: number,
    factoryId?: number
  ): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    
    const params: any = {
      workspace_type: workspaceType,
    };
    
    if (companyId) params.company_id = companyId;
    if (factoryId) params.factory_id = factoryId;
    
    const response = await api.post(
      `/welders/${welderId}/certifications/${certificationId}/upload`,
      formData,
      {
        params,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    const data = response.data.data || response.data;
    return data.url;
  }
}

// 导出单例
const certificationService = new CertificationService();
export default certificationService;

