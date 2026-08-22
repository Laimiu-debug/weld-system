import { message } from 'antd';
import apiService from './api';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  admin_level: string;
  permissions: string[];
}

const SUPER_ADMIN_PERMISSIONS = [
  'user_management',
  'enterprise_management',
  'subscription_management',
  'system_monitoring',
  'data_statistics',
  'announcement_management',
  'system_config',
  'security_management',
];

const ADMIN_PERMISSIONS = [
  'user_management',
  'data_statistics',
];

class AuthService {
  private static instance: AuthService;
  private currentUser: AuthUser | null = null;

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async login(credentials: LoginCredentials): Promise<boolean> {
    try {
      if (localStorage.getItem('admin_token') || localStorage.getItem('admin_user')) {
        this.clearAuth();
      }

      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.sdhaohan.cn/api/v1';
      const loginUrl = `${apiBaseUrl}/admin/auth/login`;

      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${encodeURIComponent(credentials.username)}&password=${encodeURIComponent(credentials.password)}`,
      });

      if (!response.ok) {
        let detail = '';
        try {
          const errBody = await response.json();
          detail = typeof errBody?.detail === 'string' ? errBody.detail : '';
        } catch {
          // ignore parse errors
        }
        if (response.status === 401 || response.status === 400) {
          message.error(detail || '用户名或密码错误');
        } else {
          message.error(detail || `登录失败（HTTP ${response.status}）`);
        }
        return false;
      }

      const authData = await response.json();
      const accessToken = authData.access_token;
      const adminData = authData.admin;

      if (typeof accessToken !== 'string' || !accessToken.includes('.') || !adminData) {
        message.error('登录失败：服务器未返回有效令牌');
        return false;
      }

      localStorage.setItem('admin_token', accessToken);

      const user: AuthUser = {
        id: adminData.id?.toString() || '',
        username: adminData.username || '',
        email: adminData.email || '',
        full_name: adminData.full_name || '',
        is_admin: true,
        admin_level: adminData.admin_level || (adminData.is_super_admin ? 'super_admin' : 'admin'),
        permissions: adminData.is_super_admin ? SUPER_ADMIN_PERMISSIONS : ADMIN_PERMISSIONS,
      };

      this.currentUser = user;
      localStorage.setItem('admin_user', JSON.stringify(user));
      return true;
    } catch {
      message.error('网络异常，无法登录，请稍后重试');
      return false;
    }
  }

  async logout(): Promise<void> {
    try {
      await apiService.authPost('/admin/auth/logout', undefined, { silent: true } as any);
    } catch {
      // 仍清除本地会话
    } finally {
      this.clearAuth();
    }
  }

  async refreshToken(): Promise<boolean> {
    try {
      const response = await apiService.authPost('/admin/auth/refresh', undefined, {
        silent: true,
      } as any);

      if (response.access_token) {
        localStorage.setItem('admin_token', response.access_token);
        return true;
      }

      return false;
    } catch {
      this.clearAuth();
      return false;
    }
  }

  getCurrentUser(): AuthUser | null {
    if (!this.currentUser) {
      const storedUser = localStorage.getItem('admin_user');
      if (storedUser) {
        try {
          this.currentUser = JSON.parse(storedUser);
        } catch {
          this.clearAuth();
        }
      }
    }
    return this.currentUser;
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('admin_token');
    const user = this.getCurrentUser();
    return !!(token && user);
  }

  hasPermission(permission: string): boolean {
    const user = this.getCurrentUser();
    return user ? user.permissions.includes(permission) || user.admin_level === 'super_admin' : false;
  }

  hasAnyPermission(permissions: string[]): boolean {
    const user = this.getCurrentUser();
    if (!user) return false;

    if (user.admin_level === 'super_admin') return true;

    return permissions.some(permission => user.permissions.includes(permission));
  }

  clearAuth(): void {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    this.currentUser = null;
  }

  async updateProfile(userData: Partial<AuthUser>): Promise<boolean> {
    try {
      const response = await apiService.put('/admin/profile', userData);

      if (response.success && response.data) {
        this.currentUser = { ...this.currentUser!, ...response.data };
        localStorage.setItem('admin_user', JSON.stringify(this.currentUser));
        return true;
      }

      return false;
    } catch {
      message.error('更新个人信息失败');
      return false;
    }
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<boolean> {
    try {
      const response = await apiService.post('/admin/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });

      if (response.success) {
        message.success('密码修改成功');
        return true;
      }

      return false;
    } catch (error: any) {
      message.error(error.response?.data?.message || '密码修改失败');
      return false;
    }
  }
}

export const authService = AuthService.getInstance();
export default authService;
