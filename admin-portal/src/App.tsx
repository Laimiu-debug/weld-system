import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthContext } from '@/contexts/AuthContext';
import AuthProvider from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import UserManagement from '@/pages/UserManagement';
import EnterpriseManagement from '@/pages/EnterpriseManagement';
import SubscriptionManagement from '@/pages/SubscriptionManagement';
import PricingManagement from '@/pages/PricingManagement';
import PaymentManagement from '@/pages/PaymentManagement';
import SystemMonitoring from '@/pages/SystemMonitoring';
import DataStatistics from '@/pages/DataStatistics';
import AnnouncementManagement from '@/pages/AnnouncementManagement';
import SystemConfig from '@/pages/SystemConfig';
import SecurityManagement from '@/pages/SecurityManagement';
import UserDetail from '@/pages/UserDetail';
import EnterpriseDetail from '@/pages/EnterpriseDetail';
import SharedLibraryManagement from '@/pages/SharedLibraryManagement';
import LoadingSpinner from '@/components/LoadingSpinner';

const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuthContext();

  if (loading) {
    return <LoadingSpinner />;
  }

  const hasLocalStorageAuth = !!(localStorage.getItem('admin_token') && localStorage.getItem('admin_user'));

  if (!isAuthenticated && !hasLocalStorageAuth) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  if (!isAuthenticated && hasLocalStorageAuth) {
    return <LoadingSpinner />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/users" element={<UserManagement />} />
        <Route path="/users/:userId" element={<UserDetail />} />
        <Route path="/enterprises" element={<EnterpriseManagement />} />
        <Route path="/enterprises/:enterpriseId" element={<EnterpriseDetail />} />
        <Route path="/subscriptions" element={<SubscriptionManagement />} />
        <Route path="/pricing" element={<PricingManagement />} />
        <Route path="/payments" element={<PaymentManagement />} />
        <Route path="/system" element={<SystemMonitoring />} />
        <Route path="/statistics" element={<DataStatistics />} />
        <Route path="/announcements" element={<AnnouncementManagement />} />
        <Route path="/config" element={<SystemConfig />} />
        <Route path="/security" element={<SecurityManagement />} />
        <Route path="/shared-library" element={<SharedLibraryManagement />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
