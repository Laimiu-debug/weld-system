// 用户相关类型
export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  phone?: string;
  avatar_url?: string;
  timezone?: string;
  language?: string;
  is_active: boolean;
  is_admin: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  membership_tier: MembershipTier;
  membership_type: MembershipType;
  subscription_status: SubscriptionStatus;
  subscription_start_date?: string;
  subscription_end_date?: string;
  subscription_expires_at?: string;
  trial_end_date?: string;
  auto_renewal: boolean;
  permissions?: {
    wps_management: boolean;
    pqr_management: boolean;
    ppqr_management: boolean;
    equipment_management: boolean;
    production_management: boolean;
    quality_management: boolean;
    materials_management: boolean;
    welders_management: boolean;
    employee_management: boolean;
    multi_factory_management: boolean;
    reports_management: boolean;
    api_access: boolean;
  };
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  preferences?: UserPreferences;
}

export type MembershipTier =
  | 'personal_free'
  | 'personal_pro'
  | 'personal_advanced'
  | 'personal_flagship'
  | 'enterprise'
  | 'enterprise_pro'
  | 'enterprise_pro_max';

export type MembershipType = 'personal' | 'enterprise';

export type SubscriptionStatus = 
  | 'active' 
  | 'expired' 
  | 'cancelled' 
  | 'pending';

export interface UserPreferences {
  theme: 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
  dashboard: {
    layout: 'grid' | 'list';
    widgets: string[];
  };
}

// 企业相关类型
export interface Company {
  id: string;
  name: string;
  description?: string;
  business_license: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  address?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  logo_url?: string;
  is_active: boolean;
  is_verified: boolean;
  subscription_status: SubscriptionStatus;
  subscription_start_date?: string;
  subscription_end_date?: string;
  trial_end_date?: string;
  auto_renewal: boolean;
  created_at: string;
  updated_at: string;
  owner_id: string;
  factories: Factory[];
  employee_count: number;
  max_employees: number;
  max_factories: number;
}

export interface Factory {
  id: string;
  name: string;
  code?: string;
  description?: string;
  address?: string;
  city?: string;
  province?: string;
  postal_code?: string;
  country?: string;
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  timezone?: string;
  established_date?: string;
  certification_info?: Record<string, any>;
  is_active: boolean;
  is_headquarters: boolean;
  created_at: string;
  updated_at: string;
  company_id: string;
}

export interface CompanyEmployee {
  id: string;
  company_id: string;
  user_id: string;
  factory_id?: string;
  role: EmployeeRole;
  permissions: Record<string, boolean>;
  is_active: boolean;
  invited_at: string;
  joined_at?: string;
  user?: User;
  factory?: Factory;
}

export type EmployeeRole = 'admin' | 'manager' | 'employee';

// WPS相关类型
export interface WPSRecord {
  id: string;
  user_id: string;
  company_id?: string;
  factory_id?: string;
  wps_number: string;
  title: string;
  version: string;
  revision: number;
  status: WPSStatus;
  priority: WPSPriority;
  standard?: string;
  specification_number?: string;
  pqr_support_uuids?: string[];
  base_material?: string;
  base_material_group?: string;
  base_material_thickness?: number;
  filler_material?: string;
  filler_material_classification?: string;
  welding_process?: string;
  welding_process_variant?: string;
  joint_type?: string;
  joint_design?: string;
  welding_position?: string;
  welding_position_progression?: string;
  preheat_temp_min?: number;
  preheat_temp_max?: number;
  interpass_temp_min?: number;
  interpass_temp_max?: number;
  // 审批相关字段
  approval_instance_id?: number;
  approval_status?: string;
  workflow_name?: string;
  can_approve?: boolean;
  can_submit_approval?: boolean;
  submitter_id?: number;
  post_weld_heat_treatment?: Record<string, any>;
  current_range?: string;
  voltage_range?: string;
  travel_speed?: string;
  heat_input_range?: string;
  gas_shield_type?: string;
  gas_flow_rate?: number;
  tungsten_electrode_type?: string;
  electrode_diameter?: number;
  technique_description?: string;
  welder_qualification_requirement?: string;
  inspection_requirements?: Record<string, any>;
  notes?: string;
  attachments?: Record<string, any>;
  tags?: string[];
  reviewed_by?: string;
  reviewed_at?: string;
  approved_by?: string;
  approved_at?: string;
  effective_date?: string;
  expiry_date?: string;
  view_count: number;
  download_count: number;
  last_viewed_at?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  user?: User;
  company?: Company;
  factory?: Factory;
}

export type WPSStatus =
  | 'draft'
  | 'review'
  | 'approved'
  | 'rejected'
  | 'archived'
  | 'obsolete';

export type WPSPriority = 
  | 'low' 
  | 'normal' 
  | 'high' 
  | 'urgent';

// PQR相关类型
export interface PQRRecord {
  id: string;
  user_id: string;
  company_id?: string;
  factory_id?: string;
  pqr_number: string;
  wps_id?: string;
  title: string;
  test_date?: string;
  status: PQRStatus;
  test_organization?: string;
  welder_name?: string;
  base_material?: string;
  filler_material?: string;
  welding_process?: string;
  tensile_strength?: number;
  yield_strength?: number;
  elongation?: number;
  impact_energy?: Record<string, any>;
  bend_test_result?: string;
  macro_examination?: string;
  notes?: string;
  attachments?: Record<string, any>;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
  factory?: Factory;
  wps?: WPSRecord;
}

export type PQRStatus = 
  | 'pending' 
  | 'qualified' 
  | 'failed';

// pPQR相关类型
export interface PPQRRecord {
  id: string;
  user_id: string;
  company_id?: string;
  ppqr_number: string;
  title: string;
  status: PPQRStatus;
  planned_test_date?: string;
  proposed_parameters?: Record<string, any>;
  review_comments?: string;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
}

export type PPQRStatus = 
  | 'draft' 
  | 'under_review' 
  | 'approved' 
  | 'rejected';

// 焊材相关类型
export interface WeldingMaterial {
  id: string;
  user_id: string;
  company_id?: string;
  factory_id?: string;
  material_code: string;
  material_name: string;
  material_type: MaterialType;
  specification?: string;
  manufacturer?: string;
  current_stock: number;
  unit: string;
  min_stock_level: number;
  storage_location?: string;
  unit_price?: number;
  currency: string;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
  factory?: Factory;
}

export type MaterialType = 
  | 'electrode' 
  | 'wire' 
  | 'flux' 
  | 'gas';

// 焊工相关类型
export interface Welder {
  id: string;
  user_id: string;
  company_id?: string;
  factory_id?: string;
  welder_code: string;
  full_name: string;
  id_number?: string;
  phone?: string;
  certification_number?: string;
  certification_level?: string;
  certification_date?: string;
  expiry_date?: string;
  qualified_processes?: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
  factory?: Factory;
}

// 设备相关类型
export interface Equipment {
  id: string;
  user_id: string;
  company_id?: string;
  factory_id?: string;
  equipment_code: string;
  equipment_name: string;
  equipment_type: EquipmentType;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  status: EquipmentStatus;
  purchase_date?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
  factory?: Factory;
}

export type EquipmentType = 
  | 'welding_machine' 
  | 'cutting_machine' 
  | 'testing_equipment'
  | 'auxiliary_equipment';

export type EquipmentStatus = 
  | 'operational' 
  | 'maintenance' 
  | 'broken' 
  | 'retired';

// 生产任务相关类型
export interface ProductionTask {
  id: string;
  user_id: string;
  company_id?: string;
  factory_id?: string;
  task_number: string;
  task_name: string;
  wps_id?: string;
  start_date?: string;
  end_date?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_welder_id?: string;
  assigned_equipment_id?: string;
  progress_percentage: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
  factory?: Factory;
  wps?: WPSRecord;
  assigned_welder?: Welder;
  assigned_equipment?: Equipment;
}

export type TaskStatus = 
  | 'pending' 
  | 'in_progress' 
  | 'completed' 
  | 'cancelled';

export type TaskPriority = 
  | 'low' 
  | 'normal' 
  | 'high' 
  | 'urgent';

// 质量检验相关类型
export interface QualityInspection {
  id: string;
  user_id: string;
  company_id?: string;
  production_task_id?: string;
  inspection_number: string;
  inspection_date: string;
  inspector_name?: string;
  inspection_type: InspectionType;
  result: InspectionResult;
  defects_found?: Record<string, any>;
  corrective_actions?: string;
  follow_up_required: boolean;
  created_at: string;
  updated_at: string;
  user?: User;
  company?: Company;
  production_task?: ProductionTask;
}

export type InspectionType = 
  | 'visual' 
  | 'radiographic' 
  | 'ultrasonic' 
  | 'magnetic_particle'
  | 'liquid_penetrant'
  | 'destructive';

export type InspectionResult = 
  | 'pass' 
  | 'fail' 
  | 'conditional';

// 通用类型
export interface PaginationParams {
  page: number;
  page_size: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
  timestamp: string;
}

// 表单相关类型
export interface FormField {
  name: string;
  label: string;
  type: 'input' | 'textarea' | 'select' | 'date' | 'number' | 'checkbox' | 'radio';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ label: string; value: any }>;
  rules?: any[];
}

// 通知相关类型
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  is_read: boolean;
  created_at: string;
  target_user_id?: string;
  target_company_id?: string;
}

export type NotificationType = 
  | 'info' 
  | 'warning' 
  | 'error' 
  | 'success' 
  | 'maintenance';

// 会员相关类型
export interface MembershipPlan {
  id: string;
  name: string;
  tier: MembershipTier;
  type: MembershipType;
  price: number;
  currency: string;
  billing_cycle: BillingCycle;
  features: string[];
  limits: MembershipLimits;
  is_popular?: boolean;
}

export type BillingCycle = 'monthly' | 'quarterly' | 'yearly';

export interface MembershipLimits {
  wps: number;
  pqr: number;
  ppqr: number;
  materials: number;
  welders: number;
  equipment: number;
  storage_mb: number;
  factories?: number;
  employees?: number;
}

// 订阅相关类型
export interface Subscription {
  id: string;
  user_id: string;
  company_id?: string;
  plan_type: MembershipTier;
  billing_cycle: BillingCycle;
  amount: number;
  currency: string;
  status: SubscriptionStatus;
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  payment_method?: string;
  payment_status: PaymentStatus;
  transaction_id?: string;
  order_id?: string;
  payment_date?: string;
  refunded_at?: string;
  refund_amount?: number;
  refund_reason?: string;
  created_at: string;
  updated_at: string;
}

export type PaymentStatus = 
  | 'pending' 
  | 'paid' 
  | 'failed' 
  | 'refunded' 
  | 'cancelled';

// 文件相关类型
export interface FileAttachment {
  id: string;
  user_id: string;
  company_id?: string;
  resource_type: string;
  resource_id: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  file_hash: string;
  description?: string;
  is_public: boolean;
  download_count: number;
  last_downloaded_at?: string;
  created_at: string;
  updated_at: string;
}

// 系统配置类型
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

// 仪表盘统计类型
export interface DashboardStats {
  wps_count: number;
  pqr_count: number;
  ppqr_count: number;
  materials_count: number;
  welders_count: number;
  equipment_count: number;
  production_count?: number;
  quality_count?: number;
  storage_used_mb: number;
  storage_limit_mb: number;
  membership_usage: {
    wps_usage: number;
    wps_limit: number;
    pqr_usage: number;
    pqr_limit: number;
    ppqr_usage: number;
    ppqr_limit: number;
  };
  company_info?: {
    name: string;
    employee_count: number;
    factory_count: number;
  };
}

// 图表数据类型
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
}

// 搜索和筛选类型
export interface SearchFilters {
  status?: string[];
  priority?: string[];
  date_range?: [string, string];
  created_by?: string;
  company_id?: string;
  factory_id?: string;
  tags?: string[];
}

// 批量操作类型
export interface BatchOperation {
  action: 'delete' | 'archive' | 'approve' | 'reject' | 'export';
  item_ids: string[];
  params?: Record<string, any>;
}

// 导出选项类型
export interface ExportOptions {
  format: 'pdf' | 'excel' | 'csv';
  fields?: string[];
  filters?: SearchFilters;
  include_attachments?: boolean;
}