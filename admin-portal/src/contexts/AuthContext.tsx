import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { message } from 'antd';
import authService, { AuthUser } from '@/services/auth';

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkPermission: (permission: string) => boolean;
  checkAnyPermission: (permissions: string[]) => boolean;
}

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: AuthUser | null }
  | { type: 'SET_AUTHENTICATED'; payload: boolean }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOGIN_SUCCESS'; payload: { user: AuthUser; token: string } };

const initialState: AuthState = {
  user: null,
  loading: true,
  isAuthenticated: false,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_USER':
      return { ...state, user: action.payload };
    case 'SET_AUTHENTICATED':
      return { ...state, isAuthenticated: action.payload };
    case 'LOGOUT':
      return { ...state, user: null, isAuthenticated: false, loading: false };
    case 'SET_LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        loading: false
      };
    default:
      return state;
  }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const navigate = useNavigate();

  console.log('AuthProvider state update:', state);

  // 初始化认证状态
  useEffect(() => {
    const initAuth = () => {
      console.log('=== AUTH PROVIDER INITIALIZATION START ===');
      console.log('AuthProvider: Initializing auth...');
      const currentUser = authService.getCurrentUser();
      const isAuth = authService.isAuthenticated();

      console.log('AuthProvider initAuth:', {
        currentUser,
        isAuth,
        hasToken: !!localStorage.getItem('admin_token'),
        hasUser: !!localStorage.getItem('admin_user'),
        timestamp: new Date().toISOString()
      });

      if (currentUser && isAuth) {
        dispatch({ type: 'SET_USER', payload: currentUser });
        dispatch({ type: 'SET_AUTHENTICATED', payload: true });
        console.log('AuthProvider: Setting authenticated user:', currentUser);
        console.log('=== AUTH PROVIDER INITIALIZATION SUCCESS ===');
      } else {
        console.log('=== AUTH PROVIDER INITIALIZATION NO USER ===');
      }

      dispatch({ type: 'SET_LOADING', payload: false });
      console.log('=== AUTH PROVIDER INITIALIZATION END ===');
    };

    initAuth();

    // 清理函数：防止 StrictMode 重复执行导致的问题
    return () => {
      console.log('=== AUTH PROVIDER CLEANUP CALLED ===');
    };
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      console.log('AuthProvider: Login starting...');
      const success = await authService.login({ username, password });
      console.log('AuthProvider: Login result:', success);

      if (success) {
        const currentUser = authService.getCurrentUser();
        const token = localStorage.getItem('admin_token');

        console.log('AuthProvider: After login - CurrentUser:', currentUser);
        console.log('AuthProvider: Token from localStorage:', token);

        if (currentUser && token) {
          // 使用单个action原子性地更新所有状态
          dispatch({
            type: 'SET_LOGIN_SUCCESS',
            payload: { user: currentUser, token }
          });

          console.log('AuthProvider: Login success action dispatched, navigating to dashboard');
          message.success('登录成功');

          // 立即导航
          navigate('/dashboard');
          return true;
        } else {
          console.error('AuthProvider: Login failed - missing user or token');
          dispatch({ type: 'SET_LOADING', payload: false });
          return false;
        }
      }

      dispatch({ type: 'SET_LOADING', payload: false });
      return false;
    } catch (error) {
      console.error('AuthProvider: Login error:', error);
      dispatch({ type: 'SET_LOADING', payload: false });
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      await authService.logout();
      dispatch({ type: 'LOGOUT' });
      message.success('已退出登录');
      navigate('/login');
    } catch (error) {
      console.error('AuthProvider: Logout error:', error);
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const checkPermission = (permission: string): boolean => {
    return authService.hasPermission(permission);
  };

  const checkAnyPermission = (permissions: string[]): boolean => {
    return authService.hasAnyPermission(permissions);
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    checkPermission,
    checkAnyPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;