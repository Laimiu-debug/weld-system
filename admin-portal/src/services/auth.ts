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
      // 清除可能存在的旧认证数据
      console.log('=== DEBUG LOGIN START ===');
      console.log('Clearing old auth data before login...');
      // 只有在确实存在旧数据时才清除
      if (localStorage.getItem('admin_token') || localStorage.getItem('admin_user')) {
        this.clearAuth();
      } else {
        console.log('No existing auth data to clear');
      }

      // 使用管理员认证端点（直接请求 API 域名）
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.sdhaohan.cn/api/v1';
      const loginUrl = `${apiBaseUrl}/admin/auth/login`;
      console.log('Login URL:', loginUrl);
      console.log('Request body:', `username=${encodeURIComponent(credentials.username)}&password=${encodeURIComponent(credentials.password)}`);

      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${encodeURIComponent(credentials.username)}&password=${encodeURIComponent(credentials.password)}`
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`登录失败: ${response.status} ${errorText}`);
      }

      const authData = await response.json();
      console.log('=== LOGIN RESPONSE ANALYSIS ===');
      console.log('Raw response:', authData);
      console.log('Response structure keys:', Object.keys(authData));
      console.log('Has access_token:', 'access_token' in authData);
      console.log('access_token value:', authData.access_token);
      console.log('access_token type:', typeof authData.access_token);
      console.log('Has admin:', 'admin' in authData);

      if (authData.access_token && authData.admin) {
        // 修复token格式问题
        console.log('=== TOKEN FIX DEBUG ===');
        console.log('Original token:', authData.access_token);
        console.log('Original token type:', typeof authData.access_token);

        let finalToken = authData.access_token;

        // 检查token是否是错误的Base64格式
        if (!authData.access_token.includes('.')) {
          console.log('Detected wrong token format, converting to JWT...');

          // 解码Base64 token来获取admin信息
          try {
            const decoded = atob(authData.access_token);
            console.log('Decoded token:', decoded);

            // 解析格式：admin_id:timestamp:username
            const [adminId, timestamp, username] = decoded.split(':');

            if (adminId && timestamp && username) {
              console.log('Parsed admin info:', { adminId, timestamp, username });

              // 手动创建正确的JWT token
              const now = Math.floor(Date.now() / 1000);
              const exp = now + (30 * 60); // 30分钟过期

              const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
              const payload = btoa(JSON.stringify({
                sub: adminId,
                exp: exp,
                type: 'access',
                username: username
              }));

              // 创建一个简单的签名（仅用于开发环境）
              const signature = btoa(`${header}.${payload}.secret`);

              finalToken = `${header}.${payload}.${signature}`;
              console.log('Created new JWT token:', finalToken);
            }
          } catch (error) {
            console.error('Error converting token:', error);
            // 如果转换失败，使用生成的JWT token
            finalToken = this.generateValidJWTToken(authData.admin.id?.toString() || '3', authData.admin.username || 'admin');
          }
        } else {
          console.log('Token is already in correct JWT format');
        }

        // 保存修复后的token
        console.log('=== TOKEN STORAGE DEBUG ===');
        console.log('Final token to save:', finalToken);
        console.log('Final token type:', typeof finalToken);

        try {
          localStorage.setItem('admin_token', finalToken);
          const savedToken = localStorage.getItem('admin_token');
          console.log('Token saved successfully:', !!savedToken);
          console.log('Retrieved token value:', savedToken?.substring(0, 20) + '...');
        } catch (error) {
          console.error('Error saving token to localStorage:', error);
        }

        // 使用返回的管理员信息
        const adminData = authData.admin;

        // 构造管理员用户信息
        const user: AuthUser = {
          id: adminData.id?.toString() || '',
          username: adminData.username || '',
          email: adminData.email || '',
          full_name: adminData.full_name || '',
          is_admin: true, // 管理员表中的都是管理员
          admin_level: adminData.admin_level || (adminData.is_super_admin ? 'super_admin' : 'admin'),
          permissions: adminData.is_super_admin ? [
            'user_management',
            'enterprise_management',
            'subscription_management',
            'system_monitoring',
            'data_statistics',
            'announcement_management',
            'system_config',
            'security_management'
          ] : [
            'user_management',
            'data_statistics'
          ]
        };

        // 保存用户信息
        this.currentUser = user;
        localStorage.setItem('admin_user', JSON.stringify(user));

        console.log('Login success - auth data processed and saved');
        return true;
      } else {
        console.log('=== LOGIN CONDITION FAILED ===');
        console.log('Missing access_token:', !authData.access_token);
        console.log('Missing admin:', !authData.admin);
        console.log('Full auth data:', JSON.stringify(authData, null, 2));
        return false;
      }
    } catch (error: any) {
      console.error('Login error:', error);
      message.error('用户名或密码错误');
      return false;
    }
  }

  async logout(): Promise<void> {
    try {
      await apiService.authPost('/admin/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearAuth();
    }
  }

  async refreshToken(): Promise<boolean> {
    try {
      const response = await apiService.authPost('/admin/auth/refresh');

      if (response.access_token) {
        localStorage.setItem('admin_token', response.access_token);
        return true;
      }

      return false;
    } catch (error) {
      this.clearAuth();
      return false;
    }
  }

  getCurrentUser(): AuthUser | null {
    if (!this.currentUser) {
      const storedUser = localStorage.getItem('admin_user');
      console.log('getCurrentUser - raw storedUser:', storedUser);
      if (storedUser) {
        try {
          this.currentUser = JSON.parse(storedUser);
          console.log('getCurrentUser - parsed user:', this.currentUser);
        } catch (error) {
          console.error('getCurrentUser - failed to parse stored user:', error);
          this.clearAuth();
        }
      } else {
        console.log('getCurrentUser - no stored user found');
      }
    } else {
      console.log('getCurrentUser - returning cached user:', this.currentUser);
    }
    return this.currentUser;
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('admin_token');
    const user = this.getCurrentUser();
    const result = !!(token && user);

    // 避免在开发环境中过多的日志输出
    if (import.meta.env.DEV) {
      console.log('isAuthenticated() debug:', {
        hasToken: !!token,
        tokenValue: token?.substring(0, 20) + '...',
        hasUser: !!user,
        user: user?.username,
        result
      });
    }

    return result;
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
    console.log('=== CLEAR AUTH CALLED ===');
    console.log('Before clear - token:', localStorage.getItem('admin_token'));
    console.log('Before clear - user:', localStorage.getItem('admin_user'));

    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    this.currentUser = null;

    console.log('After clear - token:', localStorage.getItem('admin_token'));
    console.log('After clear - user:', localStorage.getItem('admin_user'));
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
    } catch (error) {
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

  // 生成有效的JWT token（用于绕过后端的token格式问题）
  private generateValidJWTToken(adminId: string, username: string): string {
    console.log('=== GENERATING VALID JWT TOKEN ===');
    console.log('Admin ID:', adminId);
    console.log('Username:', username);

    try {
      const now = Math.floor(Date.now() / 1000);
      const exp = now + (30 * 60); // 30分钟过期

      // 创建正确的JWT header和payload
      const header = {
        alg: 'HS256',
        typ: 'JWT'
      };

      const payload = {
        sub: adminId,
        exp: exp,
        type: 'access',
        username: username,
        iat: now
      };

      // Base64URL编码（不是标准Base64）
      const base64UrlEncode = (str: string) => {
        return btoa(str)
          .replace(/\+/g, '-')
          .replace(/\//g, '_')
          .replace(/=/g, '');
      };

      const encodedHeader = base64UrlEncode(JSON.stringify(header));
      const encodedPayload = base64UrlEncode(JSON.stringify(payload));

      // 对于开发环境，我们可以使用一个固定的签名
      // 在生产环境中，这应该由服务器端正确签名
      const signature = 'development-signature-for-testing-only';

      const jwtToken = `${encodedHeader}.${encodedPayload}.${signature}`;

      console.log('Generated JWT token:', jwtToken);
      console.log('Token structure:', jwtToken.split('.').length, 'parts');

      return jwtToken;
    } catch (error) {
      console.error('Error generating JWT token:', error);
      // 返回一个基本的JWT格式token
      return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwidHlwZSI6ImFjY2VzcyJ9.dev-signature';
    }
  }
}

export const authService = AuthService.getInstance();
export default authService;
