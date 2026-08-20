import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { message } from 'antd';
import {
  mockSystemStatus,
  mockUserStatistics,
  mockSubscriptionStatistics,
  mockUsers,
  mockErrorLogs
} from './mockData';

class ApiService {
  private api: AxiosInstance;
  private authApi: AxiosInstance; // 认证API使用不同的baseURL
  private useMockData = false; // 使用真实API

  // 提供切换模拟数据的方法
  public setUseMockData(useMock: boolean) {
    this.useMockData = useMock;
  }

  public getUseMockData() {
    return this.useMockData;
  }

  constructor() {
    // 从环境变量获取 API 基础 URL，如果没有则使用相对路径
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';

    // 管理员API
    this.api = axios.create({
      baseURL: `${apiBaseUrl}/admin`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 认证API使用基础路径
    this.authApi = axios.create({
      baseURL: apiBaseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 为管理员API设置拦截器
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('admin_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.api.interceptors.response.use(
      (response) => {
        // 如果响应包含 success 和 data 字段，提取 data 字段
        if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
          return response.data.data;
        }
        return response.data;
      },
      (error) => {
        const { response } = error;

        if (response) {
          switch (response.status) {
            case 401:
              message.warning('API认证失败，请检查登录状态或联系管理员');
              break;
            case 403:
              message.error('权限不足');
              break;
            case 404:
              message.error('请求的资源不存在');
              break;
            case 500:
              message.error('服务器内部错误');
              break;
            default:
              message.error(response.data?.message || '请求失败');
          }
        } else {
          message.error('网络连接失败');
        }

        return Promise.reject(error);
      }
    );

    // 为认证API设置拦截器
    this.authApi.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('admin_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.authApi.interceptors.response.use(
      (response) => {
        // 如果响应包含 success 和 data 字段，提取 data 字段
        if (response.data && typeof response.data === 'object' && 'success' in response.data && 'data' in response.data) {
          return response.data.data;
        }
        return response.data;
      },
      (error) => {
        const { response } = error;

        if (response) {
          switch (response.status) {
            case 401:
              message.error('用户名或密码错误');
              break;
            case 403:
              message.error('权限不足');
              break;
            case 404:
              message.error('请求的资源不存在');
              break;
            case 500:
              message.error('服务器内部错误');
              break;
            default:
              message.error(response.data?.detail || '登录失败');
          }
        } else {
          message.error('网络连接失败');
        }

        return Promise.reject(error);
      }
    );
  }

  // 系统监控
  async getSystemStatus() {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockSystemStatus), 500);
      });
    }
    return this.api.get('/system/status');
  }

  async getSystemLogs(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockErrorLogs), 500);
      });
    }
    return this.api.get('/logs', { params });
  }

  async getErrorLogs(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockErrorLogs), 500);
      });
    }
    return this.api.get('/logs/errors', { params });
  }

  // 用户管理
  async getUsers(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockUsers), 500);
      });
    }
    return this.api.get('/users', { params });
  }

  async getAdmins() {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve({ items: [], total: 0 }), 500);
      });
    }
    return this.api.get('/admins');
  }

  async getUserDetail(userId: string) {
    if (this.useMockData) {
      const user = mockUsers.data.items.find(u => u.id === userId);
      return Promise.resolve({
        success: true,
        data: user
      });
    }
    return this.api.get(`/users/${userId}`);
  }

  async adjustUserMembership(userId: string, data: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            success: true,
            message: '会员等级调整成功'
          });
        }, 1000);
      });
    }
    return this.api.post(`/users/${userId}/adjust-membership`, data);
  }

  async toggleUserStatus(userId: string, isActive: boolean, reason?: string) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            success: true,
            message: `用户已${isActive ? '启用' : '禁用'}`
          });
        }, 1000);
      });
    }
    return this.api.post(`/users/${userId}/${isActive ? 'enable' : 'disable'}`, {
      reason,
    });
  }

  async deleteUser(userId: string) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            success: true,
            message: '用户删除成功'
          });
        }, 1000);
      });
    }
    return this.api.delete(`/users/${userId}`);
  }

  async verifyUserEmail(userId: string) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            success: true,
            message: '用户邮箱已验证'
          });
        }, 1000);
      });
    }
    return this.api.post(`/users/${userId}/verify-email`);
  }

  // 数据统计
  async getUserStatistics(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockUserStatistics), 500);
      });
    }
    return this.api.get('/statistics/users', { params });
  }

  async getSubscriptionStatistics(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve(mockSubscriptionStatistics), 500);
      });
    }
    return this.api.get('/statistics/subscriptions', { params });
  }

  // 其他API方法保持原有实现，但在useMockData为true时返回模拟数据
  async getEnterprises(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve({
          success: true,
          data: {
            items: [],
            total: 0,
            page: 1,
            page_size: 20,
            total_pages: 0
          }
        }), 500);
      });
    }
    return this.api.get('/enterprises', { params });
  }

  async getSubscriptions(params: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve({
          success: true,
          data: {
            items: [],
            total: 0,
            page: 1,
            page_size: 20,
            total_pages: 0
          }
        }), 500);
      });
    }
    return this.api.get('/subscriptions', { params });
  }

  // 订阅计划管理
  async getSubscriptionPlans() {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve({
          success: true,
          data: []
        }), 500);
      });
    }
    return this.api.get('/membership/subscription-plans');
  }

  async updateSubscriptionPlan(planId: string, data: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve({
          success: true,
          message: '订阅计划更新成功'
        }), 1000);
      });
    }
    return this.api.put(`/membership/subscription-plans/${planId}`, data);
  }

  async createSubscriptionPlan(data: any) {
    if (this.useMockData) {
      return new Promise(resolve => {
        setTimeout(() => resolve({
          success: true,
          message: '订阅计划创建成功'
        }), 1000);
      });
    }
    return this.api.post('/membership/subscription-plans', data);
  }

  // 认证相关方法
  async authPost<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    if (this.useMockData) {
      return Promise.resolve({ success: true, data: null } as T);
    }
    return this.authApi.post(url, data, config) as unknown as T;
  }

  async authGet<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    if (this.useMockData) {
      return Promise.resolve({ success: true, data: null } as T);
    }
    return this.authApi.get(url, config) as unknown as T;
  }

  // 通用请求方法
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    if (this.useMockData) {
      return Promise.resolve({ success: true, data: null } as T);
    }
    return this.api.get(url, config) as unknown as T;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    if (this.useMockData) {
      return Promise.resolve({ success: true, data: null } as T);
    }
    return this.api.post(url, data, config) as unknown as T;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    if (this.useMockData) {
      return Promise.resolve({ success: true, data: null } as T);
    }
    return this.api.put(url, data, config) as unknown as T;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    if (this.useMockData) {
      return Promise.resolve({ success: true, data: null } as T);
    }
    return this.api.delete(url, config) as unknown as T;
  }
}

export const apiService = new ApiService();
export default apiService;
