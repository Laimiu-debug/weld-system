/**
 * 模板管理调试页面
 * 用于诊断模板管理页面的问题
 */
import React, { useState, useEffect } from 'react'
import { Card, Button, Space, message, Spin, Alert } from 'antd'
import wpsTemplateService from '@/services/wpsTemplates'

const TemplateManagementDebug: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const testGetTemplates = async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('开始调用 getTemplates...')
      const response = await wpsTemplateService.getTemplates()
      console.log('API 响应:', response)
      setData(response)
      message.success('API 调用成功')
    } catch (err: any) {
      console.error('API 调用失败:', err)
      setError(err.message || '未知错误')
      message.error('API 调用失败: ' + (err.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title="模板管理调试">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="这是一个调试页面，用于诊断模板管理的问题"
            type="info"
            showIcon
          />

          <Button type="primary" onClick={testGetTemplates} loading={loading}>
            测试 getTemplates API
          </Button>

          {loading && <Spin />}

          {error && (
            <Alert
              message="错误"
              description={error}
              type="error"
              showIcon
            />
          )}

          {data && (
            <Card title="API 响应数据">
              <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px', overflow: 'auto' }}>
                {JSON.stringify(data, null, 2)}
              </pre>
            </Card>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default TemplateManagementDebug

