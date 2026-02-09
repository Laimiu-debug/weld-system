import React from 'react'
import { Card, Typography, Button } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

const MembershipPayment: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="page-container">
      <div className="page-header">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/membership')}
        >
          返回会员中心
        </Button>
        <Title level={2}>会员支付</Title>
      </div>

      <Card>
        <p>会员支付页面</p>
        <p>功能开发中...</p>
      </Card>
    </div>
  )
}

export default MembershipPayment

