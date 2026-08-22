import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore, bindAuthCrossTabSync } from '@/store/authStore'
import { authService } from '@/services/auth'
import Layout from '@/components/Layout'
import LoadingSpinner from '@/components/LoadingSpinner'
import { MembershipProvider } from '@/contexts/MembershipContext'

// 懒加载页面组件
const Welcome = React.lazy(() => import('@/pages/Welcome'))
const Features = React.lazy(() => import('@/pages/Features'))
const Analytics = React.lazy(() => import('@/pages/Analytics'))
const About = React.lazy(() => import('@/pages/About'))
const Login = React.lazy(() => import('@/pages/Auth/Login'))
const Register = React.lazy(() => import('@/pages/Auth/Register'))
const ForgotPassword = React.lazy(() => import('@/pages/Auth/ForgotPassword'))
const ResetPassword = React.lazy(() => import('@/pages/Auth/ResetPassword'))
const VerifyEmail = React.lazy(() => import('@/pages/Auth/VerifyEmail'))

// 法律政策页面
const PrivacyPolicy = React.lazy(() => import('@/pages/Legal/PrivacyPolicy'))
const TermsOfService = React.lazy(() => import('@/pages/Legal/TermsOfService'))
const RefundPolicy = React.lazy(() => import('@/pages/Legal/RefundPolicy'))
const PricingTerms = React.lazy(() => import('@/pages/Legal/PricingTerms'))

const Dashboard = React.lazy(() => import('@/pages/Dashboard'))

const WPSList = React.lazy(() => import('@/pages/WPS/WPSList'))
const WPSCreate = React.lazy(() => import('@/pages/WPS/WPSCreate'))
const WPSEdit = React.lazy(() => import('@/pages/WPS/WPSEdit'))
const WPSDetail = React.lazy(() => import('@/pages/WPS/WPSDetail'))
const TemplateManagement = React.lazy(() => import('@/pages/WPS/TemplateManagement'))
const ModuleManagement = React.lazy(() => import('@/pages/WPS/ModuleManagement'))
const SearchResultsPage = React.lazy(() => import('@/pages/Search/SearchResultsPage'))

const PQRList = React.lazy(() => import('@/pages/PQR/PQRList'))
const PQRCreate = React.lazy(() => import('@/pages/PQR/PQRCreate'))
const PQREdit = React.lazy(() => import('@/pages/PQR/PQREdit'))
const PQRDetail = React.lazy(() => import('@/pages/PQR/PQRDetail'))

const PPQRList = React.lazy(() => import('@/pages/pPQR/pPQRList'))
const PPQRCreate = React.lazy(() => import('@/pages/pPQR/PPQRCreate'))
const PPQREdit = React.lazy(() => import('@/pages/pPQR/PPQREdit'))
const PPQRDetail = React.lazy(() => import('@/pages/pPQR/pPQRDetail'))

const MaterialsList = React.lazy(() => import('@/pages/Materials/MaterialsList'))
const MaterialsCreate = React.lazy(() => import('@/pages/Materials/MaterialsCreate'))
const MaterialsEdit = React.lazy(() => import('@/pages/Materials/MaterialsEdit'))
const MaterialsDetail = React.lazy(() => import('@/pages/Materials/MaterialsDetail'))

const WeldersList = React.lazy(() => import('@/pages/Welders/WeldersList'))
const WeldersCreate = React.lazy(() => import('@/pages/Welders/WeldersCreate'))
const WeldersEdit = React.lazy(() => import('@/pages/Welders/WeldersEdit'))
const WeldersDetail = React.lazy(() => import('@/pages/Welders/WeldersDetail'))

const EquipmentList = React.lazy(() => import('@/pages/Equipment/EquipmentList'))
const EquipmentCreate = React.lazy(() => import('@/pages/Equipment/EquipmentCreate'))
const EquipmentEdit = React.lazy(() => import('@/pages/Equipment/EquipmentEdit'))
const EquipmentDetail = React.lazy(() => import('@/pages/Equipment/EquipmentDetail'))

const ProductionList = React.lazy(() => import('@/pages/Production/ProductionList'))
const ProductionCreate = React.lazy(() => import('@/pages/Production/ProductionCreate'))
const ProductionEdit = React.lazy(() => import('@/pages/Production/ProductionEdit'))
const ProductionDetail = React.lazy(() => import('@/pages/Production/ProductionDetail'))
const ProductionPlanManagement = React.lazy(() => import('@/pages/Production/ProductionPlanManagement'))

const QualityList = React.lazy(() => import('@/pages/Quality/QualityList'))
const QualityCreate = React.lazy(() => import('@/pages/Quality/QualityCreate'))
const QualityEdit = React.lazy(() => import('@/pages/Quality/QualityEdit'))
const QualityDetail = React.lazy(() => import('@/pages/Quality/QualityDetail'))
const QualityStandardManagement = React.lazy(() => import('@/pages/Quality/QualityStandardManagement'))

const ReportsDashboard = React.lazy(() => import('@/pages/Reports/ReportsDashboard'))
const WPSReport = React.lazy(() => import('@/pages/Reports/WPSReport'))
const PQRReport = React.lazy(() => import('@/pages/Reports/PQRReport'))
const UsageReport = React.lazy(() => import('@/pages/Reports/UsageReport'))
const CustomReportBuilder = React.lazy(() => import('@/pages/Reports/CustomReportBuilder'))

const EmployeeManagement = React.lazy(() => import('@/pages/Employees/EmployeeManagement'))
const PerformanceManagement = React.lazy(() => import('@/pages/Employees/PerformanceManagement'))

// 企业管理页面
const EnterpriseEmployees = React.lazy(() => import('@/pages/Enterprise/Employees'))
const EnterpriseFactories = React.lazy(() => import('@/pages/Enterprise/Factories'))
const EnterpriseDepartments = React.lazy(() => import('@/pages/Enterprise/Departments'))
const EnterpriseRoles = React.lazy(() => import('@/pages/Enterprise/RolesNew'))
const EnterpriseInvitations = React.lazy(() => import('@/pages/Enterprise/Invitations'))

const ProfileInfo = React.lazy(() => import('@/pages/Profile/ProfileInfo'))
const PersonalCenter = React.lazy(() => import('@/pages/Profile/PersonalCenter'))
const SystemSettings = React.lazy(() => import('@/pages/Profile/SystemSettings'))
const SecuritySettings = React.lazy(() => import('@/pages/Profile/SecuritySettings'))
const NotificationSettings = React.lazy(() => import('@/pages/Profile/NotificationSettings'))
const FeedbackBoard = React.lazy(() => import('@/pages/Feedback/FeedbackBoard'))

// 错误页面
const PermissionDenied = React.lazy(() => import('@/pages/Error/PermissionDenied'))

const MembershipCurrent = React.lazy(() => import('@/pages/Membership/MembershipCurrent'))
const MembershipUpgrade = React.lazy(() => import('@/pages/Membership/MembershipUpgrade'))
const MembershipPayment = React.lazy(() => import('@/pages/Membership/MembershipPayment'))
const PaymentResult = React.lazy(() => import('@/pages/Membership/PaymentResult'))
const SubscriptionHistory = React.lazy(() => import('@/pages/Membership/SubscriptionHistory'))

// 共享库页面
const SharedLibraryList = React.lazy(() => import('@/pages/SharedLibrary/SharedLibraryList'))

// 审批工作流页面
const ApprovalWorkflows = React.lazy(() => import('@/pages/Workflow/ApprovalWorkflows'))

// 管理端页面
const PendingPayments = React.lazy(() => import('@/pages/Admin/PendingPayments'))

// 路由守卫组件
const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredPermission?: string }> = ({
  children,
  requiredPermission,
}) => {
  const { isAuthenticated, checkPermission } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requiredPermission && !checkPermission(requiredPermission)) {
    // 显示权限不足页面而不是重定向
    return <PermissionDenied />
  }

  return <>{children}</>
}


const App: React.FC = () => {
  const { isAuthenticated, loading, setUser, setLoading } = useAuthStore()

  useEffect(() => {
    bindAuthCrossTabSync()
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      setLoading(true)
      try {
        const hasToken = authService.isAuthenticated()

        if (hasToken) {
          const user = authService.getCurrentUserFromStorage()

          if (user && user.id) {
            setUser(user)
          } else {
            try {
              const currentUser = await authService.getCurrentUser()
              if (currentUser && currentUser.id) {
                setUser(currentUser)
              } else {
                await authService.logout()
              }
            } catch {
              await authService.logout()
            }
          }
        }
      } catch {
        await authService.logout()
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [setUser, setLoading])

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <MembershipProvider>
      <React.Suspense fallback={<LoadingSpinner />}>
        <Routes>
        {/* 首页 - 未登录显示欢迎页面,已登录跳转到仪表盘 */}
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Welcome />
          }
        />

        {/* 认证路由 */}
        <Route
          path="/welcome"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Welcome />
          }
        />
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />
          }
        />
        <Route
          path="/forgot-password"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <ForgotPassword />
          }
        />
        <Route
          path="/reset-password"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <ResetPassword />
          }
        />
        <Route
          path="/verify-email"
          element={<VerifyEmail />}
        />

        {/* 法律政策路由（公开访问） */}
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/refund-policy" element={<RefundPolicy />} />
        <Route path="/pricing-info" element={<PricingTerms />} />

        {/* 公开页面路由（无需登录） */}
        <Route path="/features" element={<Features />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/about" element={<About />} />

        {/* 受保护的路由 - 需要登录才能访问,使用Layout包裹 */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          {/* 仪表盘 */}
          <Route
            path="dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* 资源库 */}
          {/* 模块管理 */}
          <Route
            path="modules"
            element={
              <ProtectedRoute>
                <ModuleManagement />
              </ProtectedRoute>
            }
          />
          {/* 模板管理 */}
          <Route
            path="templates"
            element={
              <ProtectedRoute>
                <TemplateManagement />
              </ProtectedRoute>
            }
          />
          {/* 共享库 */}
          <Route
            path="shared-library"
            element={
              <ProtectedRoute>
                <SharedLibraryList />
              </ProtectedRoute>
            }
          />


          {/* WPS管理 */}
          <Route
            path="search"
            element={
              <ProtectedRoute>
                <SearchResultsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="wps"
            element={
              <ProtectedRoute requiredPermission="wps.read">
                <WPSList />
              </ProtectedRoute>
            }
          />
          <Route
            path="wps/create"
            element={
              <ProtectedRoute requiredPermission="wps.create">
                <WPSCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="wps/:id"
            element={
              <ProtectedRoute requiredPermission="wps.read">
                <WPSDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="wps/:id/edit"
            element={
              <ProtectedRoute requiredPermission="wps.update">
                <WPSEdit />
              </ProtectedRoute>
            }
          />

          {/* PQR管理 */}
          <Route
            path="pqr"
            element={
              <ProtectedRoute requiredPermission="pqr.read">
                <PQRList />
              </ProtectedRoute>
            }
          />
          <Route
            path="pqr/create"
            element={
              <ProtectedRoute requiredPermission="pqr.create">
                <PQRCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="pqr/:id"
            element={
              <ProtectedRoute requiredPermission="pqr.read">
                <PQRDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="pqr/:id/edit"
            element={
              <ProtectedRoute requiredPermission="pqr.update">
                <PQREdit />
              </ProtectedRoute>
            }
          />

          {/* pPQR管理 */}
          <Route
            path="ppqr"
            element={
              <ProtectedRoute requiredPermission="ppqr.read">
                <PPQRList />
              </ProtectedRoute>
            }
          />
          <Route
            path="ppqr/create"
            element={
              <ProtectedRoute requiredPermission="ppqr.create">
                <PPQRCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="ppqr/:id"
            element={
              <ProtectedRoute requiredPermission="ppqr.read">
                <PPQRDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="ppqr/:id/edit"
            element={
              <ProtectedRoute requiredPermission="ppqr.update">
                <PPQREdit />
              </ProtectedRoute>
            }
          />

          {/* 焊材管理 */}
          <Route
            path="materials"
            element={
              <ProtectedRoute requiredPermission="materials.read">
                <MaterialsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="materials/create"
            element={
              <ProtectedRoute requiredPermission="materials.create">
                <MaterialsCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="materials/:id"
            element={
              <ProtectedRoute requiredPermission="materials.read">
                <MaterialsDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="materials/:id/edit"
            element={
              <ProtectedRoute requiredPermission="materials.update">
                <MaterialsEdit />
              </ProtectedRoute>
            }
          />

          {/* 焊工管理 */}
          <Route
            path="welders"
            element={
              <ProtectedRoute requiredPermission="welders.read">
                <WeldersList />
              </ProtectedRoute>
            }
          />
          <Route
            path="welders/create"
            element={
              <ProtectedRoute requiredPermission="welders.create">
                <WeldersCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="welders/:id"
            element={
              <ProtectedRoute requiredPermission="welders.read">
                <WeldersDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="welders/:id/edit"
            element={
              <ProtectedRoute requiredPermission="welders.update">
                <WeldersEdit />
              </ProtectedRoute>
            }
          />

          {/* 设备管理 */}
          <Route
            path="equipment"
            element={
              <ProtectedRoute requiredPermission="equipment.read">
                <EquipmentList />
              </ProtectedRoute>
            }
          />
          <Route
            path="equipment/create"
            element={
              <ProtectedRoute requiredPermission="equipment.create">
                <EquipmentCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="equipment/:id"
            element={
              <ProtectedRoute requiredPermission="equipment.read">
                <EquipmentDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="equipment/:id/edit"
            element={
              <ProtectedRoute requiredPermission="equipment.update">
                <EquipmentEdit />
              </ProtectedRoute>
            }
          />

          {/* 生产管理 */}
          <Route
            path="production"
            element={
              <ProtectedRoute requiredPermission="production.read">
                <ProductionList />
              </ProtectedRoute>
            }
          />
          <Route
            path="production/plans"
            element={
              <ProtectedRoute requiredPermission="production.read">
                <ProductionPlanManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="production/create"
            element={
              <ProtectedRoute requiredPermission="production.create">
                <ProductionCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="production/:id"
            element={
              <ProtectedRoute requiredPermission="production.read">
                <ProductionDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="production/:id/edit"
            element={
              <ProtectedRoute requiredPermission="production.update">
                <ProductionEdit />
              </ProtectedRoute>
            }
          />

          {/* 质量管理 */}
          <Route
            path="quality"
            element={
              <ProtectedRoute requiredPermission="quality.read">
                <QualityList />
              </ProtectedRoute>
            }
          />
          <Route
            path="quality/standards"
            element={
              <ProtectedRoute requiredPermission="quality.read">
                <QualityStandardManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="quality/create"
            element={
              <ProtectedRoute requiredPermission="quality.create">
                <QualityCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="quality/:id"
            element={
              <ProtectedRoute requiredPermission="quality.read">
                <QualityDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="quality/:id/edit"
            element={
              <ProtectedRoute requiredPermission="quality.update">
                <QualityEdit />
              </ProtectedRoute>
            }
          />

          {/* 报表统计 */}
          <Route
            path="reports"
            element={
              <ProtectedRoute requiredPermission="reports.read">
                <ReportsDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="reports/wps"
            element={
              <ProtectedRoute requiredPermission="reports.read">
                <WPSReport />
              </ProtectedRoute>
            }
          />
          <Route
            path="reports/pqr"
            element={
              <ProtectedRoute requiredPermission="reports.read">
                <PQRReport />
              </ProtectedRoute>
            }
          />
          <Route
            path="reports/usage"
            element={
              <ProtectedRoute requiredPermission="reports.read">
                <UsageReport />
              </ProtectedRoute>
            }
          />
          <Route
            path="reports/custom"
            element={
              <ProtectedRoute requiredPermission="reports.read">
                <CustomReportBuilder />
              </ProtectedRoute>
            }
          />

          {/* 企业管理 */}
          <Route
            path="enterprise/employees"
            element={
              <ProtectedRoute requiredPermission="enterprise.employees">
                <EnterpriseEmployees />
              </ProtectedRoute>
            }
          />
          <Route
            path="enterprise/factories"
            element={
              <ProtectedRoute requiredPermission="enterprise.factories">
                <EnterpriseFactories />
              </ProtectedRoute>
            }
          />
          <Route
            path="enterprise/departments"
            element={
              <ProtectedRoute requiredPermission="enterprise.departments">
                <EnterpriseDepartments />
              </ProtectedRoute>
            }
          />
          <Route
            path="enterprise/roles"
            element={
              <ProtectedRoute requiredPermission="enterprise.roles">
                <EnterpriseRoles />
              </ProtectedRoute>
            }
          />
          <Route
            path="enterprise/invitations"
            element={
              <ProtectedRoute requiredPermission="enterprise.invitations">
                <EnterpriseInvitations />
              </ProtectedRoute>
            }
          />
          <Route
            path="enterprise/approval-workflows"
            element={
              <ProtectedRoute requiredPermission="enterprise.roles">
                <ApprovalWorkflows />
              </ProtectedRoute>
            }
          />

          {/* 员工管理 */}
          <Route
            path="employees"
            element={
              <ProtectedRoute requiredPermission="employees.read">
                <EmployeeManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="employees/performance"
            element={
              <ProtectedRoute requiredPermission="employees.read">
                <PerformanceManagement />
              </ProtectedRoute>
            }
          />

          {/* 个人中心 */}
          <Route
            path="profile"
            element={
              <ProtectedRoute>
                <PersonalCenter />
              </ProtectedRoute>
            }
          />
          <Route
            path="profile/info"
            element={
              <ProtectedRoute>
                <ProfileInfo />
              </ProtectedRoute>
            }
          />
          <Route
            path="profile/settings"
            element={
              <ProtectedRoute>
                <SystemSettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="profile/security"
            element={
              <ProtectedRoute>
                <SecuritySettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="profile/notifications"
            element={
              <ProtectedRoute>
                <NotificationSettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="feedback"
            element={
              <ProtectedRoute>
                <FeedbackBoard />
              </ProtectedRoute>
            }
          />

          {/* 会员管理 */}
          <Route
            path="membership"
            element={
              <ProtectedRoute>
                <MembershipCurrent />
              </ProtectedRoute>
            }
          />
          <Route
            path="membership/upgrade"
            element={
              <ProtectedRoute>
                <MembershipUpgrade />
              </ProtectedRoute>
            }
          />
          <Route
            path="membership/payment"
            element={
              <ProtectedRoute>
                <MembershipPayment />
              </ProtectedRoute>
            }
          />
          <Route
            path="membership/result"
            element={
              <ProtectedRoute>
                <PaymentResult />
              </ProtectedRoute>
            }
          />
          <Route
            path="membership/history"
            element={
              <ProtectedRoute>
                <SubscriptionHistory />
              </ProtectedRoute>
            }
          />

          {/* 管理后台 */}
          <Route
            path="admin/pending-payments"
            element={
              <ProtectedRoute>
                <PendingPayments />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* 404页面 - 未登录跳转到欢迎页,已登录跳转到仪表盘 */}
        <Route
          path="*"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/" replace />
          }
        />
      </Routes>
      </React.Suspense>
    </MembershipProvider>
  )
}

export default App