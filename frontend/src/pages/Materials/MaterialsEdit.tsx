import React from 'react'
import { useParams } from 'react-router-dom'
import { Card, Typography, Button } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

const MaterialsEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <div className="page-container">
      <div className="page-header">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/materials')}
        >
          返回列表
        </Button>
        <Title level={2}>编辑焊材</Title>
      </div>

      <Card>
        <p>焊材编辑页面 - ID: {id}</p>
      </Card>
    </div>
  )
}

export default MaterialsEdit