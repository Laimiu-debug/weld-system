import React, { useState, useEffect, useRef } from 'react'
import { Row, Col, Button, Drawer, Space } from 'antd'
import {
  MenuOutlined,
  CloseOutlined,
  LeftOutlined,
  RightOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons'

interface ResponsiveContainerProps {
  children: React.ReactNode
  sidebar?: React.ReactNode
  header?: React.ReactNode
  className?: string
  breakpoint?: 'sm' | 'md' | 'lg' | 'xl' | 'xxl'
}

interface ResponsiveGridProps {
  children: React.ReactNode
  cols?: { xs?: number; sm?: number; md?: number; lg?: number; xl?: number; xxl?: number }
  gutter?: [number, number] | number
  className?: string
}

interface ResponsiveCardProps {
  children: React.ReactNode
  title?: React.ReactNode
  extra?: React.ReactNode
  className?: string
  collapsible?: boolean
  bordered?: boolean
}

interface ResponsiveTableProps {
  columns: any[]
  dataSource: any[]
  loading?: boolean
  pagination?: any
  className?: string
  scroll?: { x?: number; y?: number }
}

const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  sidebar,
  header,
  className = '',
  breakpoint = 'lg',
}) => {
  const [isMobile, setIsMobile] = useState(false)
  const [sidebarVisible, setSidebarVisible] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth
      const breakpoints = {
        sm: 576,
        md: 768,
        lg: 992,
        xl: 1200,
        xxl: 1600,
      }
      setIsMobile(width < breakpoints[breakpoint])
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [breakpoint])

  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible)
  }

  if (isMobile) {
    return (
      <div className={`responsive-container mobile ${className}`} ref={containerRef}>
        {header && (
          <div className="mobile-header">
            {sidebar && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={toggleSidebar}
                className="sidebar-toggle"
              />
            )}
            {header}
          </div>
        )}

        <Drawer
          title={null}
          placement="left"
          onClose={toggleSidebar}
          open={sidebarVisible}
          styles={{ body: { padding: 0 } }}
          closable={false}
          extra={
            <Button
              type="text"
              icon={<CloseOutlined />}
              onClick={toggleSidebar}
            />
          }
        >
          {sidebar}
        </Drawer>

        <div className="mobile-content">
          {children}
        </div>
      </div>
    )
  }

  return (
    <div className={`responsive-container desktop ${className}`} ref={containerRef}>
      <div className="desktop-layout">
        {sidebar && (
          <div className="desktop-sidebar">
            {sidebar}
          </div>
        )}
        <div className="desktop-main">
          {header && (
            <div className="desktop-header">
              {header}
            </div>
          )}
          <div className="desktop-content">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  cols = { xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 6 },
  gutter = [16, 16],
  className = '',
}) => {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  if (isMobile) {
    return (
      <div className={`responsive-grid mobile ${className}`}>
        {React.Children.map(children, (child, index) => (
          <div key={index} className="mobile-grid-item">
            {child}
          </div>
        ))}
      </div>
    )
  }

  return (
    <Row gutter={gutter} className={`responsive-grid desktop ${className}`}>
      {React.Children.map(children, (child, index) => (
        <Col key={index} {...cols}>
          {child}
        </Col>
      ))}
    </Row>
  )
}

const ResponsiveCard: React.FC<ResponsiveCardProps> = ({
  children,
  title,
  extra,
  className = '',
  collapsible = false,
  bordered = true,
}) => {
  const [collapsed, setCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  const toggleCollapse = () => {
    setCollapsed(!collapsed)
  }

  if (isMobile) {
    return (
      <div className={`responsive-card mobile ${className}`}>
        {(title || extra) && (
          <div className="mobile-card-header">
            <div className="mobile-card-title">
              {title}
            </div>
            <div className="mobile-card-extra">
              <Space>
                {collapsible && (
                  <Button
                    type="text"
                    size="small"
                    icon={collapsed ? <RightOutlined /> : <LeftOutlined />}
                    onClick={toggleCollapse}
                  />
                )}
                {extra}
              </Space>
            </div>
          </div>
        )}
        <div className={`mobile-card-content ${collapsed ? 'collapsed' : ''}`}>
          {children}
        </div>
      </div>
    )
  }

  return (
    <div className={`responsive-card desktop ${className} ${bordered ? 'bordered' : ''}`}>
      {(title || extra) && (
        <div className="desktop-card-header">
          <div className="desktop-card-title">
            {title}
          </div>
          <div className="desktop-card-extra">
            <Space>
              {collapsible && (
                <Button
                  type="text"
                  size="small"
                  icon={collapsed ? <RightOutlined /> : <LeftOutlined />}
                  onClick={toggleCollapse}
                />
              )}
              {extra}
            </Space>
          </div>
        </div>
      )}
      <div className={`desktop-card-content ${collapsed ? 'collapsed' : ''}`}>
        {children}
      </div>
    </div>
  )
}

const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  columns,
  dataSource,
  loading = false,
  pagination,
  className = '',
  scroll,
}) => {
  const [isMobile, setIsMobile] = useState(false)
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  const handleRowClick = (record: any) => {
    if (isMobile) {
      setExpandedRow(expandedRow === record.id ? null : record.id)
    }
  }

  // 移动端渲染卡片视图
  const renderMobileView = () => {
    return (
      <div className={`responsive-table mobile ${className}`}>
        {dataSource.map((record, index) => (
          <div key={record.id || index} className="mobile-table-row">
            <div
              className="mobile-table-header"
              onClick={() => handleRowClick(record)}
            >
              <div className="mobile-table-title">
                {columns[0] && record[columns[0].dataIndex]}
              </div>
              <Button
                type="text"
                size="small"
                icon={expandedRow === record.id ? <UpOutlined /> : <DownOutlined />}
              />
            </div>
            {expandedRow === record.id && (
              <div className="mobile-table-content">
                {columns.slice(1).map((col, colIndex) => (
                  <div key={colIndex} className="mobile-table-field">
                    <div className="mobile-table-label">{col.title}</div>
                    <div className="mobile-table-value">
                      {col.render ? col.render(record[col.dataIndex], record) : record[col.dataIndex]}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  if (isMobile) {
    return renderMobileView()
  }

  return (
    <div className={`responsive-table desktop ${className}`}>
      <Table
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        pagination={pagination}
        scroll={scroll}
        size="middle"
      />
    </div>
  )
}

// 响应式工具函数
export const useResponsive = () => {
  const [screenSize, setScreenSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  })
  const [isMobile, setIsMobile] = useState(false)
  const [isTablet, setIsTablet] = useState(false)
  const [isDesktop, setIsDesktop] = useState(false)

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      const height = window.innerHeight

      setScreenSize({ width, height })
      setIsMobile(width < 768)
      setIsTablet(width >= 768 && width < 1024)
      setIsDesktop(width >= 1024)
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return {
    screenSize,
    isMobile,
    isTablet,
    isDesktop,
  }
}

// 响应式断点Hook
export const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState<'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl'>('lg')

  useEffect(() => {
    const getBreakpoint = () => {
      const width = window.innerWidth
      if (width < 576) return 'xs'
      if (width < 768) return 'sm'
      if (width < 992) return 'md'
      if (width < 1200) return 'lg'
      if (width < 1600) return 'xl'
      return 'xxl'
    }

    const handleResize = () => {
      setBreakpoint(getBreakpoint())
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return breakpoint
}

export {
  ResponsiveContainer,
  ResponsiveGrid,
  ResponsiveCard,
  ResponsiveTable,
}