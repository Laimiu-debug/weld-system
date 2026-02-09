/**
 * 焊接接头示意图生成器 V4 字段组件
 * 用于在WPS模块中集成V4版本的示意图生成器
 */
import React, { useState } from 'react'
import { Button, Space, Upload, Modal, message, UploadFile } from 'antd'
import { PictureOutlined, UploadOutlined, ToolOutlined } from '@ant-design/icons'
import WeldJointDiagramGeneratorV4, { WeldJointParamsV4 } from './WeldJointDiagramGeneratorV4'

interface WeldJointDiagramV4FieldProps {
  value?: UploadFile[]
  onChange?: (fileList: UploadFile[]) => void
  disabled?: boolean
  label?: string
  // 从表单中获取的参数
  formValues?: Partial<WeldJointParamsV4>
}

const WeldJointDiagramV4Field: React.FC<WeldJointDiagramV4FieldProps> = ({
  value = [],
  onChange,
  disabled = false,
  label = '焊接接头示意图',
  formValues
}) => {
  const [modalVisible, setModalVisible] = useState(false)

  // 调试：打印接收到的 value
  React.useEffect(() => {
    console.log('[WeldJointDiagramV4Field] 接收到的 value:', {
      length: value?.length || 0,
      hasValue: value && value.length > 0,
      firstImage: value && value.length > 0 ? {
        uid: value[0].uid,
        name: value[0].name,
        status: value[0].status,
        hasUrl: !!value[0].url,
        hasThumbUrl: !!value[0].thumbUrl,
        urlType: value[0].url?.startsWith('data:image') ? 'base64' : value[0].url?.startsWith('blob:') ? 'blob' : 'unknown',
        urlPreview: (value[0].url || value[0].thumbUrl)?.substring(0, 50)
      } : null
    })
  }, [value])
  const [generatorParams, setGeneratorParams] = useState<WeldJointParamsV4>({
    grooveType: 'V',
    groovePosition: 'outer',
    alignment: 'centerline',
    leftThickness: 12,
    leftGrooveAngle: 30,
    leftGrooveDepth: 10,
    leftBevel: false,
    leftBevelPosition: 'outer',
    leftBevelLength: 15,
    leftBevelHeight: 2,
    rightThickness: 10,
    rightGrooveAngle: 30,
    rightGrooveDepth: 8,
    rightBevel: false,
    rightBevelPosition: 'outer',
    rightBevelLength: 15,
    rightBevelHeight: 2,
    bluntEdge: 2,
    rootGap: 2,
  })

  // 当模态框打开时，从表单值中初始化参数
  React.useEffect(() => {
    if (modalVisible && formValues) {
      setGeneratorParams(prev => ({
        ...prev,
        grooveType: formValues.grooveType || prev.grooveType,
        groovePosition: formValues.groovePosition || prev.groovePosition,
        alignment: formValues.alignment || prev.alignment,
        leftThickness: formValues.leftThickness || prev.leftThickness,
        leftGrooveAngle: formValues.leftGrooveAngle || prev.leftGrooveAngle,
        leftGrooveDepth: formValues.leftGrooveDepth || prev.leftGrooveDepth,
        leftBevel: formValues.leftBevel || prev.leftBevel,
        leftBevelPosition: formValues.leftBevelPosition || prev.leftBevelPosition,
        leftBevelLength: formValues.leftBevelLength || prev.leftBevelLength,
        leftBevelHeight: formValues.leftBevelHeight || prev.leftBevelHeight,
        rightThickness: formValues.rightThickness || prev.rightThickness,
        rightGrooveAngle: formValues.rightGrooveAngle || prev.rightGrooveAngle,
        rightGrooveDepth: formValues.rightGrooveDepth || prev.rightGrooveDepth,
        rightBevel: formValues.rightBevel || prev.rightBevel,
        rightBevelPosition: formValues.rightBevelPosition || prev.rightBevelPosition,
        rightBevelLength: formValues.rightBevelLength || prev.rightBevelLength,
        rightBevelHeight: formValues.rightBevelHeight || prev.rightBevelHeight,
        bluntEdge: formValues.bluntEdge || prev.bluntEdge,
        rootGap: formValues.rootGap || prev.rootGap,
      }))
    }
  }, [modalVisible, formValues])

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
      name: `weld_joint_v4_${Date.now()}.png`,
      status: 'done',
      url: base64Url,  // 使用 base64 URL，这样在页面刷新后仍然有效
      thumbUrl: base64Url
      // 不包含 originFileObj，避免序列化问题
    }

    console.log('[WeldJointDiagramV4Field] 生成图表成功:', {
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

  // 获取 base64
  const getBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = error => reject(error)
    })
  }

  // 处理文件删除
  const handleRemove = () => {
    onChange?.([])
  }

  return (
    <div>
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 图片预览 */}
        {value && value.length > 0 && (
          <div style={{ marginBottom: 8 }}>
            <img
              src={value[0].url || value[0].thumbUrl}
              alt={label}
              style={{ maxWidth: '100%', maxHeight: 300, border: '1px solid #d9d9d9', borderRadius: 4 }}
              onError={(e) => {
                console.error('[WeldJointDiagramV4Field] 图片加载失败:', {
                  src: value[0].url || value[0].thumbUrl,
                  value: value[0]
                });
                // 尝试使用备用URL
                const target = e.target as HTMLImageElement;
                if (target.src !== value[0].thumbUrl && value[0].thumbUrl) {
                  target.src = value[0].thumbUrl;
                }
              }}
            />
          </div>
        )}

        {/* 操作按钮 */}
        <Space>
          <Button
            icon={<ToolOutlined />}
            onClick={() => setModalVisible(true)}
            disabled={disabled}
          >
            自动生成
          </Button>
          
          <Upload
            disabled={disabled}
            maxCount={1}
            accept="image/*"
            showUploadList={false}
            beforeUpload={() => false}
            onChange={handleUploadChange}
          >
            <Button icon={<UploadOutlined />} disabled={disabled}>
              上传图片
            </Button>
          </Upload>

          {value && value.length > 0 && (
            <Button danger onClick={handleRemove} disabled={disabled}>
              删除
            </Button>
          )}
        </Space>
      </Space>

      {/* 生成器模态框 */}
      <Modal
        title="焊接接头示意图生成器 V4"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={1200}
        destroyOnClose
      >
        <WeldJointDiagramGeneratorV4 
          onGenerate={handleGenerate}
          initialParams={generatorParams}
        />
      </Modal>
    </div>
  )
}

export default WeldJointDiagramV4Field

