/**
 * 图表字段组件
 * 支持手动上传图片和自动生成图表两种方式
 */
import React, { useState } from 'react'
import { Upload, Button, Space, Modal, Tabs, Image, message } from 'antd'
import { UploadOutlined, PictureOutlined, ToolOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import DiagramGenerator from './DiagramGenerator'

interface DiagramFieldProps {
  value?: UploadFile[]
  onChange?: (value: UploadFile[]) => void
  diagramType: 'groove' | 'weld_layer'  // 图表类型
  label: string
  disabled?: boolean
}

const DiagramField: React.FC<DiagramFieldProps> = ({
  value,
  onChange,
  diagramType,
  label,
  disabled = false
}) => {
  const [modalVisible, setModalVisible] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)

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
      name: `${diagramType}_${Date.now()}.png`,
      status: 'done',
      url: base64Url,  // 使用 base64 URL，这样在页面刷新后仍然有效
      thumbUrl: base64Url
      // 不包含 originFileObj，避免序列化问题
    }

    console.log('[DiagramField] 生成图表成功:', {
      name: uploadFile.name,
      urlType: 'base64',
      urlLength: base64Url.length
    })

    // 更新值
    onChange?.([uploadFile])
    setModalVisible(false)
    message.success('图表生成成功！')
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

  return (
    <>
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
              <PictureOutlined />
              <div style={{ marginTop: 8 }}>上传图片</div>
            </div>
          )}
        </Upload>
        
        {!disabled && (
          <Button
            icon={<ToolOutlined />}
            onClick={() => setModalVisible(true)}
            block
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
        width={900}
        footer={null}
      >
        <DiagramGenerator
          type={diagramType}
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

export default DiagramField

