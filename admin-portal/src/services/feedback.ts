import api from './api';

export interface AdminFeedbackItem {
  id: number;
  user_id: number;
  user_email?: string | null;
  user_name?: string | null;
  title: string;
  content: string;
  contact?: string | null;
  is_read: boolean;
  read_at?: string | null;
  admin_note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FeedbackListResponse {
  items: AdminFeedbackItem[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
}

export const getFeedbackList = async (params?: {
  page?: number;
  page_size?: number;
  is_read?: boolean;
}): Promise<FeedbackListResponse> => {
  return api.get('/feedback', { params });
};

export const markFeedbackRead = async (id: number): Promise<AdminFeedbackItem> => {
  return api.post(`/feedback/${id}/mark-read`);
};

export const updateFeedbackNote = async (
  id: number,
  admin_note: string
): Promise<AdminFeedbackItem> => {
  return api.patch(`/feedback/${id}`, { admin_note });
};

export const deleteFeedback = async (id: number): Promise<void> => {
  await api.delete(`/feedback/${id}`);
};
