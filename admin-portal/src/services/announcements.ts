import api from './api';
import { SystemAnnouncement } from '@/types';

export interface AnnouncementListResponse {
  items: SystemAnnouncement[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateAnnouncementData {
  title: string;
  content: string;
  announcement_type: 'info' | 'warning' | 'error' | 'success' | 'maintenance';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  target_audience: 'all' | 'user' | 'enterprise';
  is_pinned?: boolean;
  publish_at?: string;
  expire_at?: string;
}

export interface UpdateAnnouncementData extends Partial<CreateAnnouncementData> {
  id: number;
}

/**
 * 获取公告列表
 */
export const getAnnouncements = async (params?: {
  page?: number;
  page_size?: number;
  is_published?: boolean;
  announcement_type?: string;
  is_auto_generated?: boolean;
}): Promise<AnnouncementListResponse> => {
  const response = await api.get('/system/announcements', { params });
  return response;
};

/**
 * 获取公告详情
 */
export const getAnnouncementById = async (id: number): Promise<SystemAnnouncement> => {
  const response = await api.get(`/system/announcements/${id}`);
  return response;
};

/**
 * 创建公告
 */
export const createAnnouncement = async (data: CreateAnnouncementData): Promise<SystemAnnouncement> => {
  const response = await api.post('/system/announcements', data);
  return response;
};

/**
 * 更新公告
 */
export const updateAnnouncement = async (id: number, data: Partial<CreateAnnouncementData>): Promise<SystemAnnouncement> => {
  const response = await api.put(`/system/announcements/${id}`, data);
  return response;
};

/**
 * 删除公告
 */
export const deleteAnnouncement = async (id: number): Promise<void> => {
  await api.delete(`/system/announcements/${id}`);
};

/**
 * 发布公告
 */
export const publishAnnouncement = async (id: number): Promise<void> => {
  await api.post(`/system/announcements/${id}/publish`);
};

/**
 * 取消发布公告
 */
export const unpublishAnnouncement = async (id: number): Promise<void> => {
  await api.post(`/system/announcements/${id}/unpublish`);
};

// ==================== 自动通知任务 ====================

export const runDailyNotificationTasks = async (): Promise<{
  expiring_count: number;
  expired_count: number;
  renewed_count: number;
  quota_count: number;
  total_notifications: number;
}> => {
  const response = await api.post('/system/notifications/tasks/daily');
  return response;
};

export const runExpiringNotificationTask = async (daysAhead: number = 7): Promise<{
  count: number;
  days_ahead: number;
}> => {
  const response = await api.post(`/system/notifications/tasks/expiring?days_ahead=${daysAhead}`);
  return response;
};

export const runQuotaNotificationTask = async (): Promise<{
  count: number;
}> => {
  const response = await api.post('/system/notifications/tasks/quota');
  return response;
};

export default {
  getAnnouncements,
  getAnnouncementById,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  publishAnnouncement,
  unpublishAnnouncement,
};

