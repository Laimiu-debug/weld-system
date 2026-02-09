/**
 * 焊接接头示意图字段组件
 * 支持手动上传图片和自动生成示意图两种方式
 */
import React, { useState } from 'react'
import { Upload, Button, Space, Modal, Tabs, Image, message, Card, Empty } from 'antd'
import { UploadOutlined, PictureOutlined, ToolOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import WeldJointDiagramGenerator from './WeldJointDiagramGenerator'

interface WeldJointDiagramFieldProps {
  value?: UploadFile[]
  onChange?: (value: UploadFile[]) => void
  label?: string
  disabled?: boolean
}

const WeldJointDiagramField: React.FC<WeldJointDiagramFieldProps> = ({
  value,
  onChange,
  label = '焊接接头示意图',
  disabled = false
}) => {
  const [modalVisible, setModalVisible] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'upload' | 'generate'>('upload')

  // 处理图表生成
  const handleGenerate = (canvas: HTMLCanvasElement) => {
    // 将 canvas 直接转换为 base64 URL（不使用 blob URL，因为 blob URL 在页面刷新后会失效）
    const base64Url = canvas.toDataURL('image/png')

    if (!base64Url) {
      message.error('生成图表失败')
      return
    }

    // 创建 UploadFile 对象，直接使用 base64 URL
    const uploadFile: UploadFile = {
      uid: `-${Date.now()}`,
      name: `weld_joint_diagram_${Date.now()}.png`,
      status: 'done',
      url: base64Url,  // 使用 base64 URL，这样在页面刷新后仍然有效
      thumbUrl: base64Url
      // 不包含 originFileObj，避免序列化问题
    }

    console.log('[WeldJointDiagramField] 生成图表成功:', {
      name: uploadFile.name,
      urlType: 'base64',
      urlLength: base64Url.length
    })

    // 更新值
    onChange?.([uploadFile])
    setModalVisible(false)
    message.success('焊接接头示意图生成成功！')
  }

  // 处理文件上传
  const handleUploadChange = async (info: any) => {
    let fileList = [...info.fileList]

    // 只保留最新的一个文件
    fileList = fileList.slice(-1)

    // 将上传的文件转换为 base64
    if (fileList.length > 0 && fileList[0].originFileObj) {
      try {
        const base64 = await getBase64(fileList[0].originFileObj)
        fileList[0].url = base64
        fileList[0].thumbUrl = base64
      } catch (error) {
        console.error('转换图片为base64失败:', error)
      }
    }

    // 更新文件列表
    onChange?.(fileList)
  }

  // 处理预览
  const handlePreview = async (file: UploadFile) => {
    if (!file.url && !file.preview) {
      file.preview = await getBase64(file.originFileObj as any)
    }
    setPreviewImage(file.url || file.preview || '')
  }

  // 获取 base64
  const getBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = error => reject(error)
    })
  }

  // 删除图片
  const handleRemove = () => {
    onChange?.([])
  }

  return (
    <>
      <Card 
        title={label}
        size="small"
        style={{ marginBottom: 16 }}
      >
        {value && value.length > 0 ? (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Image
                src={value[0].url || value[0].thumbUrl || value[0].preview}
                alt="preview"
                style={{ maxWidth: '100%', maxHeight: 300, borderRadius: '4px' }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RUG8O+L"
                onError={(e) => {
                  console.error('[WeldJointDiagramField] 图片加载失败:', {
                    src: value[0].url || value[0].thumbUrl || value[0].preview,
                    error: e
                  });
                  // 尝试使用备用URL
                  const target = e.target as HTMLImageElement;
                  if (target.src !== value[0].thumbUrl && value[0].thumbUrl) {
                    target.src = value[0].thumbUrl;
                  } else if (target.src !== value[0].preview && value[0].preview) {
                    target.src = value[0].preview;
                  }
                }}
              />
            </div>
            <Space>
              <Button 
                type="primary" 
                onClick={() => handlePreview(value[0])}
              >
                查看大图
              </Button>
              <Button 
                danger 
                onClick={handleRemove}
                disabled={disabled}
              >
                删除
              </Button>
            </Space>
          </div>
        ) : (
          <Empty 
            description="未上传或生成示意图"
            style={{ marginBottom: 16 }}
          />
        )}
      </Card>

      <Space direction="vertical" style={{ width: '100%' }}>
        <Upload
          listType="picture-card"
          fileList={value || []}
          onChange={handleUploadChange}
          onPreview={handlePreview}
          beforeUpload={() => false}  // 阻止自动上传
          maxCount={1}
          accept="image/*"
          disabled={disabled}
        >
          {(!value || value.length === 0) && (
            <div>
              <UploadOutlined />
              <div style={{ marginTop: 8 }}>上传图片</div>
            </div>
          )}
        </Upload>
        
        {!disabled && (
          <Button
            icon={<ToolOutlined />}
            onClick={() => setModalVisible(true)}
            block
            size="large"
          >
            自动生成{label}
          </Button>
        )}
      </Space>

      {/* 图表生成器模态框 */}
      <Modal
        title={`生成${label}`}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        width={1000}
        footer={null}
      >
        <WeldJointDiagramGenerator
          onGenerate={handleGenerate}
        />
      </Modal>

      {/* 图片预览模态框 */}
      <Modal
        open={!!previewImage}
        title="图片预览"
        footer={null}
        onCancel={() => setPreviewImage(null)}
      >
        <Image
          alt="preview"
          style={{ width: '100%' }}
          src={previewImage || ''}
        />
      </Modal>
    </>
  )
}

export default WeldJointDiagramField

