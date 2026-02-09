export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  membership_tier: 'free' | 'personal_pro' | 'personal_advanced' | 'personal_flagship' | 'enterprise';
  membership_type: 'personal' | 'enterprise';
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login_at?: string;
  subscription_expires_at?: string;
  is_inherited_from_company?: boolean;  // 是否通过企业继承会员权限
  company_name?: string;  // 所属企业名称（如果是继承的）
  // 配额信息
  quotas: {
    wps_limit: number;
    pqr_limit: number;
    ppqr_limit: number;
    current_wps: number;
    current_pqr: number;
    current_ppqr: number;
  };
}

export interface Enterprise {
  id: string;
  name: string;
  description?: string;
  business_license: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  admin_user_id: string;
  factories: Factory[];
  employee_count: number;
}

export interface Factory {
  id: string;
  name: string;
  description?: string;
  address: string;
  is_active: boolean;
  created_at: string;
  enterprise_id: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan_tier: string;
  amount: number;
  currency: string;
  status: 'active' | 'cancelled' | 'expired' | 'pending';
  started_at: string;
  expires_at: string;
  created_at: string;
  auto_renew: boolean;
}

export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error';
  uptime_seconds: number;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  database_status: 'connected' | 'disconnected';
  redis_status: 'connected' | 'disconnected';
  active_users: number;
  api_requests_per_minute: number;
}

export interface SystemLog {
  id: string;
  log_level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  log_type: 'api' | 'database' | 'security' | 'system';
  message: string;
  details?: Record<string, any>;
  user_id?: string;
  ip_address?: string;
  user_agent?: string;
  request_method?: string;
  request_path?: string;
  request_params?: Record<string, any>;
  response_status?: number;
  response_time?: number;
  error_message?: string;
  stack_trace?: string;
  created_at: string;
}

export interface SystemAnnouncement {
  id: number;
  title: string;
  content: string;
  announcement_type: 'info' | 'warning' | 'error' | 'success' | 'maintenance';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  is_published: boolean;
  is_pinned: boolean;
  is_auto_generated?: boolean;  // 是否为系统自动生成
  target_audience: 'all' | 'user' | 'enterprise';
  publish_at?: string;
  expire_at?: string;
  view_count: number;
  created_at: string;
  created_by?: number;  // 可选，自动生成的公告可能没有创建者
  updated_at?: string;
  updated_by?: number;
}

export interface UserStatistics {
  total_users: number;
  new_users: number;
  active_users: number;
  by_tier: Record<string, number>;
  growth_rate: number;
  trend: Array<{
    date: string;
    count: number;
  }>;
}

export interface SubscriptionStatistics {
  total_subscriptions: number;
  active_subscriptions: number;
  new_subscriptions: number;
  cancelled_subscriptions: number;
  revenue: {
    monthly: number;
    total: number;
    by_tier: Record<string, number>;
  };
  conversion_rate: number;
  churn_rate: number;
}

export interface SystemConfig {
  maintenance_mode: boolean;
  registration_enabled: boolean;
  max_upload_size_mb: number;
  session_timeout_minutes: number;
  email_service_enabled: boolean;
  storage_service_enabled: boolean;
  backup_enabled: boolean;
  auto_backup_interval_hours: number;
  log_retention_days: number;
}

export interface Admin {
  id: string;
  user_id: string;
  admin_level: 'super_admin' | 'admin';
  permissions: string[];
  is_active: boolean;
  created_at: string;
  created_by?: string;
}

export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}