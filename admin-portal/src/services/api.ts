import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { message } from 'antd';

class ApiService {
  private api: AxiosInstance;
  private authApi: AxiosInstance;

  constructor() {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';

    this.api = axios.create({
      baseURL: `${apiBaseUrl}/admin`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

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
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('admin_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.api.interceptors.response.use(
      (response) => {
        if (
          response.data &&
          typeof response.data === 'object' &&
          'success' in response.data &&
          'data' in response.data
        ) {
          return response.data.data;
        }
        return response.data;
      },
      (error) => {
        if (error?.config?.silent) {
          return Promise.reject(error);
        }
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

    this.authApi.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('admin_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.authApi.interceptors.response.use(
      (response) => {
        if (
          response.data &&
          typeof response.data === 'object' &&
          'success' in response.data &&
          'data' in response.data
        ) {
          return response.data.data;
        }
        return response.data;
      },
      (error) => {
        if (error?.config?.silent) {
          return Promise.reject(error);
        }
        const { response } = error;

        if (response) {
          switch (response.status) {
            case 401: {
              const url = String(error.config?.url || '');
              const isLoginRequest = /\/admin\/auth\/login(\?|$)/.test(url);
              message.error(
                isLoginRequest
                  ? '用户名或密码错误'
                  : '登录已过期，请重新登录'
              );
              break;
            }
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
              message.error(response.data?.detail || '请求失败');
          }
        } else {
          message.error('网络连接失败');
        }

        return Promise.reject(error);
      }
    );
  }

  async getSystemStatus() {
    return this.api.get('/system/status');
  }

  async getSystemLogs(params: any) {
    return this.api.get('/logs', { params });
  }

  async getErrorLogs(params: any) {
    return this.api.get('/logs/errors', { params });
  }

  async getUsers(params: any) {
    return this.api.get('/users', { params });
  }

  async getAdmins() {
    return this.api.get('/admins');
  }

  async getUserDetail(userId: string) {
    return this.api.get(`/users/${userId}`);
  }

  async adjustUserMembership(userId: string, data: any) {
    return this.api.post(`/users/${userId}/adjust-membership`, data);
  }

  async toggleUserStatus(userId: string, isActive: boolean, reason?: string) {
    return this.api.post(`/users/${userId}/${isActive ? 'enable' : 'disable'}`, {
      reason,
    });
  }

  async deleteUser(userId: string) {
    return this.api.delete(`/users/${userId}`);
  }

  async verifyUserEmail(userId: string) {
    return this.api.post(`/users/${userId}/verify-email`);
  }

  async getUserStatistics(params: any) {
    return this.api.get('/statistics/users', { params });
  }

  async getSubscriptionStatistics(params: any) {
    return this.api.get('/statistics/subscriptions', { params });
  }

  async getEnterprises(params: any) {
    return this.api.get('/enterprises', { params });
  }

  async getEnterpriseDetail<T = any>(companyId: string): Promise<T> {
    return this.api.get(`/enterprises/${companyId}`) as unknown as Promise<T>;
  }

  async getSubscriptions(params: any) {
    return this.api.get('/subscriptions', { params });
  }

  async getSubscriptionPlans() {
    return this.api.get('/membership/subscription-plans');
  }

  async updateSubscriptionPlan(planId: string, data: any) {
    return this.api.put(`/membership/subscription-plans/${planId}`, data);
  }

  async createSubscriptionPlan(data: any) {
    return this.api.post('/membership/subscription-plans', data);
  }

  async authPost<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.authApi.post(url, data, config) as unknown as T;
  }

  async authGet<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.authApi.get(url, config) as unknown as T;
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.api.get(url, config) as unknown as T;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.api.post(url, data, config) as unknown as T;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.api.put(url, data, config) as unknown as T;
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.api.patch(url, data, config) as unknown as T;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.api.delete(url, config) as unknown as T;
  }
}

export const apiService = new ApiService();
export default apiService;
