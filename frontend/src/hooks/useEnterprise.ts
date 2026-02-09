import { useState, useEffect, useCallback } from 'react'
import { message } from 'antd'
import enterpriseService, {
  type CompanyEmployee,
  type Factory,
  type Department,
  type EmployeeInvitation,
  type EmployeeQuota,
  type InviteEmployeeData,
  type CreateFactoryData,
  type CreateDepartmentData,
} from '@/services/enterprise'

// 企业员工管理Hook
export const useEnterpriseEmployees = (params?: {
  page?: number
  page_size?: number
  status?: string
  role?: string
  factory_id?: string
  search?: string
}) => {
  const [employees, setEmployees] = useState<CompanyEmployee[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [current, setCurrent] = useState(1)

  const loadEmployees = useCallback(async () => {
    setLoading(true)
    try {
      const response = await enterpriseService.getEmployees(params)
      console.log('📊 员工列表响应:', response)
      console.log('📊 响应数据:', response?.data)

      if (response?.data?.success && response?.data?.data) {
        const employeeData = response.data.data
        console.log('📊 员工数据:', employeeData)
        setEmployees(employeeData.items || [])
        setTotal(employeeData.total || 0)
        setCurrent(employeeData.page || 1)
      } else if (response?.data) {
        // 兼容旧格式
        setEmployees(response.data.items || [])
        setTotal(response.data.total || 0)
        setCurrent(response.data.page || 1)
      }
    } catch (error) {
      message.error('加载员工列表失败')
      console.error('Load employees error:', error)
      // 设置默认值避免无限循环
      setEmployees([])
      setTotal(0)
      setCurrent(1)
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])

  useEffect(() => {
    loadEmployees()
  }, [loadEmployees])

  const inviteEmployee = useCallback(async (data: InviteEmployeeData) => {
    try {
      await enterpriseService.inviteEmployee(data)
      message.success('邀请发送成功')
      return true
    } catch (error) {
      message.error('邀请发送失败')
      console.error('Invite employee error:', error)
      return false
    }
  }, [])

  const updateEmployeePermissions = useCallback(async (
    employeeId: string,
    data: {
      role?: string
      permissions?: Record<string, boolean>
      data_access_scope?: string
      factory_id?: string
      department_id?: string
    }
  ) => {
    try {
      await enterpriseService.updateEmployeePermissions(employeeId, data)
      message.success('权限更新成功')
      loadEmployees()
      return true
    } catch (error) {
      message.error('权限更新失败')
      console.error('Update permissions error:', error)
      return false
    }
  }, [loadEmployees])

  const deactivateEmployee = useCallback(async (employeeId: string) => {
    try {
      await enterpriseService.deactivateEmployee(employeeId)
      message.success('员工已停用')
      loadEmployees()
      return true
    } catch (error) {
      message.error('停用失败')
      console.error('Deactivate employee error:', error)
      return false
    }
  }, [loadEmployees])

  const activateEmployee = useCallback(async (employeeId: string) => {
    try {
      await enterpriseService.activateEmployee(employeeId)
      message.success('员工已激活')
      loadEmployees()
      return true
    } catch (error) {
      message.error('激活失败')
      console.error('Activate employee error:', error)
      return false
    }
  }, [loadEmployees])

  const deleteEmployee = useCallback(async (employeeId: string) => {
    try {
      await enterpriseService.deleteEmployee(employeeId)
      message.success('员工已删除')
      loadEmployees()
      return true
    } catch (error) {
      message.error('删除失败')
      console.error('Delete employee error:', error)
      return false
    }
  }, [loadEmployees])

  return {
    employees,
    loading,
    total,
    current,
    loadEmployees,
    inviteEmployee,
    updateEmployeePermissions,
    deactivateEmployee,
    activateEmployee,
    deleteEmployee,
  }
}

// 工厂管理Hook
export const useEnterpriseFactories = (params?: {
  page?: number
  page_size?: number
  is_active?: boolean
}) => {
  const [factories, setFactories] = useState<Factory[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)

  const loadFactories = useCallback(async () => {
    setLoading(true)
    try {
      console.log('🔍 开始加载工厂列表，参数:', params)
      const response = await enterpriseService.getFactories(params)
      console.log('📦 工厂列表API响应:', response)
      console.log('📊 响应数据结构:', {
        data: response?.data,
        dataData: response?.data?.data,
        items: response?.data?.data?.items,
        total: response?.data?.data?.total
      })

      setFactories(response.data.data?.items || [])
      setTotal(response.data.data?.total || 0)
      console.log('✅ 工厂列表加载完成，工厂数量:', response.data.data?.items?.length || 0)
    } catch (error) {
      console.error('❌ 加载工厂列表失败:', error)
      message.error('加载工厂列表失败')
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])

  useEffect(() => {
    loadFactories()
  }, [loadFactories])

  const createFactory = useCallback(async (data: CreateFactoryData) => {
    try {
      console.log('🏭 开始创建工厂，数据:', data)
      await enterpriseService.createFactory(data)
      console.log('✅ 工厂创建成功，重新加载工厂列表')
      message.success('工厂创建成功')
      loadFactories()
      return true
    } catch (error) {
      console.error('❌ 工厂创建失败:', error)
      message.error('工厂创建失败')
      return false
    }
  }, [loadFactories])

  const updateFactory = useCallback(async (factoryId: string, data: Partial<CreateFactoryData>) => {
    try {
      await enterpriseService.updateFactory(factoryId, data)
      message.success('工厂更新成功')
      loadFactories()
      return true
    } catch (error) {
      message.error('工厂更新失败')
      console.error('Update factory error:', error)
      return false
    }
  }, [loadFactories])

  const deleteFactory = useCallback(async (factoryId: string) => {
    try {
      await enterpriseService.deleteFactory(factoryId)
      message.success('工厂删除成功')
      loadFactories()
      return true
    } catch (error) {
      message.error('工厂删除失败')
      console.error('Delete factory error:', error)
      return false
    }
  }, [loadFactories])

  const toggleFactoryStatus = useCallback(async (factoryId: string, isActive: boolean) => {
    try {
      await enterpriseService.updateFactory(factoryId, { is_active: isActive })
      message.success(isActive ? '工厂已启用' : '工厂已停用')
      loadFactories()
      return true
    } catch (error) {
      message.error(isActive ? '启用失败' : '停用失败')
      console.error('Toggle factory status error:', error)
      return false
    }
  }, [loadFactories])

  return {
    factories,
    loading,
    total,
    loadFactories,
    createFactory,
    updateFactory,
    deleteFactory,
    toggleFactoryStatus,
  }
}

// 部门管理Hook
export const useEnterpriseDepartments = (params?: {
  page?: number
  page_size?: number
  factory_id?: string
}) => {
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)

  const loadDepartments = useCallback(async () => {
    setLoading(true)
    try {
      console.log('🔍 开始加载部门列表，参数:', params)
      const response = await enterpriseService.getDepartments(params)
      console.log('📦 部门列表API响应:', response)
      console.log('📊 响应数据结构:', {
        data: response?.data,
        dataData: response?.data?.data,
        items: response?.data?.data?.items,
        total: response?.data?.data?.total
      })

      setDepartments(response.data.data?.items || [])
      setTotal(response.data.data?.total || 0)
      console.log('✅ 部门列表加载完成，部门数量:', response.data.data?.items?.length || 0)
    } catch (error) {
      console.error('❌ 加载部门列表失败:', error)
      message.error('加载部门列表失败')
      // 设置默认值避免无限循环
      setDepartments([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])

  useEffect(() => {
    loadDepartments()
  }, [loadDepartments])

  const createDepartment = useCallback(async (data: CreateDepartmentData) => {
    try {
      await enterpriseService.createDepartment(data)
      message.success('部门创建成功')
      loadDepartments()
      return true
    } catch (error) {
      message.error('部门创建失败')
      console.error('Create department error:', error)
      return false
    }
  }, [loadDepartments])

  const updateDepartment = useCallback(async (departmentId: string, data: Partial<CreateDepartmentData>) => {
    try {
      await enterpriseService.updateDepartment(departmentId, data)
      message.success('部门更新成功')
      loadDepartments()
      return true
    } catch (error) {
      message.error('部门更新失败')
      console.error('Update department error:', error)
      return false
    }
  }, [loadDepartments])

  const deleteDepartment = useCallback(async (departmentId: string) => {
    try {
      await enterpriseService.deleteDepartment(departmentId)
      message.success('部门删除成功')
      loadDepartments()
      return true
    } catch (error) {
      message.error('部门删除失败')
      console.error('Delete department error:', error)
      return false
    }
  }, [loadDepartments])

  return {
    departments,
    loading,
    total,
    loadDepartments,
    createDepartment,
    updateDepartment,
    deleteDepartment,
  }
}

// 邀请管理Hook
export const useEnterpriseInvitations = (params?: {
  page?: number
  page_size?: number
  status?: string
}) => {
  const [invitations, setInvitations] = useState<EmployeeInvitation[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)

  const loadInvitations = useCallback(async () => {
    setLoading(true)
    try {
      const response = await enterpriseService.getInvitations(params)
      setInvitations(response.data.items || [])
      setTotal(response.data.total || 0)
    } catch (error) {
      message.error('加载邀请列表失败')
      console.error('Load invitations error:', error)
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])

  useEffect(() => {
    loadInvitations()
  }, [loadInvitations])

  const cancelInvitation = useCallback(async (invitationId: string) => {
    try {
      await enterpriseService.cancelInvitation(invitationId)
      message.success('邀请已取消')
      loadInvitations()
      return true
    } catch (error) {
      message.error('取消邀请失败')
      console.error('Cancel invitation error:', error)
      return false
    }
  }, [loadInvitations])

  const resendInvitation = useCallback(async (invitationId: string) => {
    try {
      await enterpriseService.resendInvitation(invitationId)
      message.success('邀请已重新发送')
      return true
    } catch (error) {
      message.error('重新发送失败')
      console.error('Resend invitation error:', error)
      return false
    }
  }, [])

  return {
    invitations,
    loading,
    total,
    loadInvitations,
    cancelInvitation,
    resendInvitation,
  }
}

// 员工配额Hook
export const useEmployeeQuota = () => {
  const [quota, setQuota] = useState<EmployeeQuota | null>(null)
  const [loading, setLoading] = useState(false)

  const loadQuota = useCallback(async () => {
    setLoading(true)
    try {
      const response = await enterpriseService.getEmployeeQuota()
      setQuota(response.data)
    } catch (error) {
      message.error('加载配额信息失败')
      console.error('Load quota error:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadQuota()
  }, [loadQuota])

  return {
    quota,
    loading,
    loadQuota,
  }
}

// 员工统计Hook
export const useEmployeeStatistics = () => {
  const [statistics, setStatistics] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const loadStatistics = useCallback(async () => {
    setLoading(true)
    try {
      const response = await enterpriseService.getEmployeeStatistics()
      setStatistics(response.data)
    } catch (error) {
      message.error('加载统计信息失败')
      console.error('Load statistics error:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStatistics()
  }, [loadStatistics])

  return {
    statistics,
    loading,
    loadStatistics,
  }
}