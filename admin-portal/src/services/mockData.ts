// Mock data exports
export const mockSystemStatus = {
  success: true,
  data: {
    status: 'healthy',
    uptime_seconds: 86400,
    cpu_usage: 45.2,
    memory_usage: 62.8,
    disk_usage: 38.5,
    database_status: 'connected',
    redis_status: 'connected',
    active_users: 150,
    api_requests_per_minute: 320
  }
};

export const mockUserStatistics = {
  success: true,
  data: {
    total_users: 1500,
    new_users: 150,
    active_users: 800,
    by_tier: {
      free: 800,
      personal_pro: 400,
      personal_advanced: 200,
      personal_flagship: 50,
      enterprise: 50
    },
    growth_rate: 11.1,
    trend: [
      { date: '2025-09-01', count: 1350 },
      { date: '2025-09-15', count: 1400 },
      { date: '2025-10-01', count: 1450 },
      { date: '2025-10-16', count: 1500 }
    ]
  }
};

export const mockSubscriptionStatistics = {
  success: true,
  data: {
    total_subscriptions: 450,
    active_subscriptions: 420,
    new_subscriptions: 75,
    cancelled_subscriptions: 5,
    revenue: {
      monthly: 50000,
      total: 500000,
      by_tier: {
        personal_pro: 15000,
        personal_advanced: 20000,
        personal_flagship: 10000,
        enterprise: 5000
      }
    },
    conversion_rate: 15.5,
    churn_rate: 2.1
  }
};

export const mockUsers = {
  success: true,
  data: {
    items: [
      {
        id: 'user-001',
        email: 'user1@example.com',
        username: 'user1',
        full_name: '张三',
        membership_tier: 'free',
        membership_type: 'personal',
        is_active: true,
        is_admin: false,
        created_at: '2025-09-01T10:00:00Z',
        last_login_at: '2025-10-16T09:30:00Z',
        subscription_expires_at: null,
        quotas: {
          wps_limit: 10,
          pqr_limit: 10,
          ppqr_limit: 0,
          current_wps: 3,
          current_pqr: 2,
          current_ppqr: 0
        }
      },
      {
        id: 'user-002',
        email: 'user2@example.com',
        username: 'user2',
        full_name: '李四',
        membership_tier: 'personal_pro',
        membership_type: 'personal',
        is_active: true,
        is_admin: false,
        created_at: '2025-09-05T14:30:00Z',
        last_login_at: '2025-10-15T16:45:00Z',
        subscription_expires_at: '2025-11-05T14:30:00Z',
        quotas: {
          wps_limit: 30,
          pqr_limit: 30,
          ppqr_limit: 30,
          current_wps: 15,
          current_pqr: 12,
          current_ppqr: 8
        }
      },
      {
        id: 'user-003',
        email: 'user3@example.com',
        username: 'user3',
        full_name: '王五',
        membership_tier: 'enterprise',
        membership_type: 'enterprise',
        is_active: true,
        is_admin: false,
        created_at: '2025-09-10T09:15:00Z',
        last_login_at: '2025-10-16T08:20:00Z',
        subscription_expires_at: '2025-10-10T09:15:00Z',
        quotas: {
          wps_limit: 200,
          pqr_limit: 200,
          ppqr_limit: 200,
          current_wps: 45,
          current_pqr: 38,
          current_ppqr: 25
        }
      },
      {
        id: 'user-004',
        email: 'user4@example.com',
        username: 'user4',
        full_name: '赵六',
        membership_tier: 'personal_flagship',
        membership_type: 'personal',
        is_active: false,
        is_admin: false,
        created_at: '2025-08-20T11:00:00Z',
        last_login_at: '2025-10-10T15:30:00Z',
        subscription_expires_at: '2025-09-20T11:00:00Z',
        quotas: {
          wps_limit: 100,
          pqr_limit: 100,
          ppqr_limit: 100,
          current_wps: 0,
          current_pqr: 0,
          current_ppqr: 0
        }
      }
    ],
    total: 4,
    page: 1,
    page_size: 20,
    total_pages: 1
  }
};

export const mockErrorLogs = {
  success: true,
  data: {
    items: [
      {
        id: 'log-001',
        log_level: 'error',
        log_type: 'api',
        message: 'Database connection timeout',
        details: { query: 'SELECT * FROM users', duration: 5000 },
        user_id: 'user-001',
        ip_address: '192.168.1.100',
        request_method: 'GET',
        request_path: '/api/users',
        response_status: 500,
        response_time: 5.2,
        error_message: 'Connection timeout after 5000ms',
        created_at: '2025-10-16T10:30:00Z'
      },
      {
        id: 'log-002',
        log_level: 'warning',
        log_type: 'system',
        message: 'High memory usage detected',
        details: { usage: '85%', threshold: '80%' },
        user_id: null,
        ip_address: null,
        request_method: null,
        request_path: null,
        response_status: null,
        response_time: null,
        created_at: '2025-10-16T10:15:00Z'
      }
    ],
    total: 2,
    page: 1,
    page_size: 10,
    total_pages: 1
  }
};
