import { apiService } from './api';
import { ModuleInstance } from './wpsTemplates';

// 共享库相关类型定义
export interface LibrarySearchQuery {
  keyword?: string;
  category?: string;
  difficulty_level?: string;
  tags?: string[];
  status?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
  featured_only?: boolean;
  welding_process?: string;
  standard?: string;
}

export interface SharedModule {
  id: string;
  original_module_id: string;
  name: string;
  description?: string;
  icon: string;
  module_type: string;  // wps/pqr/ppqr/common
  category: string;
  repeatable: boolean;
  fields: any;
  uploader_id: number;
  uploader_name?: string;
  upload_time: string;
  version: string;
  changelog?: string;
  download_count: number;
  like_count: number;
  dislike_count: number;
  view_count: number;
  status: string;
  reviewer_id?: number;
  reviewer_name?: string;
  review_time?: string;
  review_comment?: string;
  is_featured: boolean;
  featured_order: number;
  tags: string[];
  difficulty_level: string;
  created_at: string;
  updated_at: string;
  user_rating?: string;
}

export interface SharedTemplate {
  id: string;
  original_template_id: string;
  name: string;
  description?: string;
  module_type: string;  // wps/pqr/ppqr
  welding_process?: string;
  welding_process_name?: string;
  standard?: string;
  module_instances: ModuleInstance[];
  uploader_id: number;
  uploader_name?: string;
  upload_time: string;
  version: string;
  changelog?: string;
  download_count: number;
  like_count: number;
  dislike_count: number;
  view_count: number;
  status: string;
  reviewer_id?: number;
  reviewer_name?: string;
  review_time?: string;
  review_comment?: string;
  is_featured: boolean;
  featured_order: number;
  tags: string[];
  difficulty_level: string;
  industry_type?: string;
  created_at: string;
  updated_at: string;
  user_rating?: string;
}

export interface SharedModuleCreate {
  original_module_id: string;
  name: string;
  description?: string;
  icon?: string;
  category?: string;
  repeatable?: boolean;
  fields?: any;
  tags?: string[];
  difficulty_level?: string;
  changelog?: string;
}

export interface SharedTemplateCreate {
  original_template_id: string;
  name: string;
  description?: string;
  welding_process?: string;
  welding_process_name?: string;
  standard?: string;
  module_instances: ModuleInstance[];
  tags?: string[];
  difficulty_level?: string;
  industry_type?: string;
  changelog?: string;
}

export interface UserRatingCreate {
  target_type: 'module' | 'template';
  target_id: string;
  rating_type: 'like' | 'dislike';
}

export interface SharedCommentCreate {
  target_type: 'module' | 'template';
  target_id: string;
  content: string;
  parent_id?: string;
}

export interface SharedComment {
  id: string;
  user_id: number;
  user_name?: string;
  target_type: string;
  target_id: string;
  content: string;
  parent_id?: string;
  status: string;
  created_at: string;
  updated_at: string;
  replies?: SharedComment[];
}

export interface LibraryStats {
  total_modules: number;
  total_templates: number;
  approved_modules: number;
  approved_templates: number;
  pending_modules: number;
  pending_templates: number;
  total_downloads: number;
  total_ratings: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// 共享库API服务类
export class SharedLibraryService {
  // ==================== 共享模块相关API ====================

  static async shareModule(moduleData: SharedModuleCreate): Promise<SharedModule> {
    const response = await apiService.post('/shared-library/modules/share', moduleData);
    return response.data;
  }

  static async getSharedModules(query: LibrarySearchQuery): Promise<PaginatedResponse<SharedModule>> {
    const response = await apiService.get('/shared-library/modules', { params: query });
    return response.data;
  }

  static async getSharedModule(moduleId: string): Promise<SharedModule> {
    const response = await apiService.get(`/shared-library/modules/${moduleId}`);
    return response.data;
  }

  static async downloadSharedModule(moduleId: string): Promise<any> {
    // 工作区上下文通过 X-Workspace-ID header 自动传递
    const response = await apiService.post(`/shared-library/modules/${moduleId}/download`);
    return response.data;
  }

  static async updateSharedModule(moduleId: string, moduleData: Partial<SharedModuleCreate>): Promise<SharedModule> {
    const response = await apiService.put(`/shared-library/modules/${moduleId}`, moduleData);
    return response.data;
  }

  static async deleteSharedModule(moduleId: string): Promise<{ message: string }> {
    const response = await apiService.delete(`/shared-library/modules/${moduleId}`);
    return response.data;
  }

  // ==================== 共享模板相关API ====================

  static async shareTemplate(templateData: SharedTemplateCreate): Promise<SharedTemplate> {
    const response = await apiService.post('/shared-library/templates/share', templateData);
    return response.data;
  }

  static async getSharedTemplates(query: LibrarySearchQuery): Promise<PaginatedResponse<SharedTemplate>> {
    const response = await apiService.get('/shared-library/templates', { params: query });
    return response.data;
  }

  static async getSharedTemplate(templateId: string): Promise<SharedTemplate> {
    const response = await apiService.get(`/shared-library/templates/${templateId}`);
    return response.data;
  }

  static async downloadSharedTemplate(templateId: string): Promise<any> {
    // 工作区上下文通过 X-Workspace-ID header 自动传递
    const response = await apiService.post(`/shared-library/templates/${templateId}/download`);
    return response.data;
  }

  static async updateSharedTemplate(templateId: string, templateData: Partial<SharedTemplateCreate>): Promise<SharedTemplate> {
    const response = await apiService.put(`/shared-library/templates/${templateId}`, templateData);
    return response.data;
  }

  static async deleteSharedTemplate(templateId: string): Promise<{ message: string }> {
    const response = await apiService.delete(`/shared-library/templates/${templateId}`);
    return response.data;
  }

  // ==================== 评分相关API ====================

  static async rateSharedResource(ratingData: UserRatingCreate): Promise<{ message: string; rating_type: string }> {
    const response = await apiService.post('/shared-library/rate', ratingData);
    return response.data;
  }

  // ==================== 评论相关API ====================

  static async createComment(commentData: SharedCommentCreate): Promise<SharedComment> {
    const response = await apiService.post('/shared-library/comments', commentData);
    return response.data;
  }

  static async getComments(
    targetType: 'module' | 'template',
    targetId: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<SharedComment>> {
    const response = await apiService.get(`/shared-library/comments/${targetType}/${targetId}`, {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }

  // ==================== 管理员API ====================

  static async reviewSharedResource(
    resourceType: 'module' | 'template',
    resourceId: string,
    reviewAction: { status: string; review_comment?: string }
  ): Promise<{ message: string }> {
    const response = await apiService.post(`/shared-library/admin/review/${resourceType}/${resourceId}`, reviewAction);
    return response.data;
  }

  static async setFeaturedResource(
    resourceType: 'module' | 'template',
    resourceId: string,
    featuredAction: { is_featured: boolean; featured_order?: number }
  ): Promise<{ message: string }> {
    const response = await apiService.post(`/shared-library/admin/featured/${resourceType}/${resourceId}`, featuredAction);
    return response.data;
  }

  static async getLibraryStats(): Promise<LibraryStats> {
    const response = await apiService.get('/shared-library/admin/stats');
    return response.data;
  }

  static async getPendingResources(
    resourceType: 'module' | 'template',
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<SharedModule | SharedTemplate>> {
    const response = await apiService.get(`/shared-library/admin/pending/${resourceType}`, {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }
}