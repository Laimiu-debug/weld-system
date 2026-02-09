/**
 * 图表生成器
 * 根据参数自动生成坡口图、焊层焊道图等技术图表
 */
import React, { useRef, useEffect } from 'react'
import { Card, Row, Col, Form, Input, InputNumber, Select, Button, Space, message } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'

interface DiagramGeneratorProps {
  type: 'groove' | 'weld_layer'  // 图表类型
  onGenerate?: (canvas: HTMLCanvasElement) => void
}

interface GrooveParams {
  grooveType: 'V' | 'U' | 'J' | 'X'  // 坡口类型
  grooveAngle: number  // 坡口角度
  rootGap: number  // 根部间隙
  thickness: number  // 厚度
}

interface WeldLayerParams {
  layerCount: number  // 焊层数量
  passPerLayer: number  // 每层焊道数
}

const DiagramGenerator: React.FC<DiagramGeneratorProps> = ({ type, onGenerate }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [form] = Form.useForm()
  const [grooveParams, setGrooveParams] = React.useState<GrooveParams>({
    grooveType: 'V',
    grooveAngle: 60,
    rootGap: 2,
    thickness: 10
  })
  const [weldParams, setWeldParams] = React.useState<WeldLayerParams>({
    layerCount: 3,
    passPerLayer: 2
  })

  // 绘制坡口图
  const drawGrooveDiagram = React.useCallback((canvas: HTMLCanvasElement, params: GrooveParams) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2
    const centerY = height / 2

    // 清空画布
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, width, height)

    // 绘制边框
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 1
    ctx.strokeRect(0, 0, width, height)

    // 绘制坡口
    ctx.strokeStyle = '#1890ff'
    ctx.lineWidth = 2
    ctx.fillStyle = 'rgba(24, 144, 255, 0.1)'

    const scale = 10  // 缩放因子
    const thickness = params.thickness * scale
    const rootGap = params.rootGap * scale
    const angle = (params.grooveAngle * Math.PI) / 180

    ctx.beginPath()
    ctx.moveTo(centerX - thickness / 2, centerY - thickness / 2)
    ctx.lineTo(centerX + thickness / 2, centerY - thickness / 2)

    // 根据坡口类型绘制
    switch (params.grooveType) {
      case 'V':
        ctx.lineTo(centerX + rootGap / 2, centerY + thickness / 2)
        ctx.lineTo(centerX - rootGap / 2, centerY + thickness / 2)
        break
      case 'U':
        ctx.quadraticCurveTo(centerX + thickness / 2, centerY, centerX + rootGap / 2, centerY + thickness / 2)
        ctx.lineTo(centerX - rootGap / 2, centerY + thickness / 2)
        ctx.quadraticCurveTo(centerX - thickness / 2, centerY, centerX - thickness / 2, centerY - thickness / 2)
        break
      case 'J':
        ctx.lineTo(centerX + thickness / 2, centerY)
        ctx.lineTo(centerX + rootGap / 2, centerY + thickness / 2)
        ctx.lineTo(centerX - rootGap / 2, centerY + thickness / 2)
        break
      case 'X':
        ctx.lineTo(centerX + rootGap / 2, centerY + thickness / 2)
        ctx.lineTo(centerX - rootGap / 2, centerY + thickness / 2)
        ctx.lineTo(centerX - thickness / 2, centerY - thickness / 2)
        break
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    // 绘制标注
    ctx.fillStyle = '#000'
    ctx.font = '12px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(`坡口类型: ${params.grooveType}型`, centerX, 20)
    ctx.fillText(`坡口角度: ${params.grooveAngle}°`, centerX, 40)
    ctx.fillText(`根部间隙: ${params.rootGap}mm`, centerX, 60)
    ctx.fillText(`厚度: ${params.thickness}mm`, centerX, 80)
  }, [])

  // 绘制焊层焊道图
  const drawWeldLayerDiagram = React.useCallback((canvas: HTMLCanvasElement, params: WeldLayerParams) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height

    // 清空画布
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, width, height)

    // 绘制边框
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 1
    ctx.strokeRect(0, 0, width, height)

    const layerHeight = (height - 100) / params.layerCount
    const colors = ['#ff7a45', '#ff9c6e', '#ffa940', '#ffc069', '#ffd666']

    // 绘制每一层
    for (let i = 0; i < params.layerCount; i++) {
      const y = 50 + i * layerHeight
      ctx.fillStyle = colors[i % colors.length]
      ctx.fillRect(50, y, width - 100, layerHeight - 10)
      ctx.strokeStyle = '#000'
      ctx.lineWidth = 1
      ctx.strokeRect(50, y, width - 100, layerHeight - 10)

      // 绘制焊道
      const passWidth = (width - 100) / params.passPerLayer
      for (let j = 0; j < params.passPerLayer; j++) {
        const x = 50 + j * passWidth + passWidth / 2
        ctx.fillStyle = '#000'
        ctx.font = '10px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(`${j + 1}`, x, y + layerHeight / 2)
      }

      // 绘制层号
      ctx.fillStyle = '#000'
      ctx.font = 'bold 12px Arial'
      ctx.textAlign = 'right'
      ctx.fillText(`第${i + 1}层`, 40, y + layerHeight / 2)
    }

    // 绘制标题
    ctx.fillStyle = '#000'
    ctx.font = 'bold 14px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(`焊层焊道图 (${params.layerCount}层, 每层${params.passPerLayer}道)`, width / 2, 30)
  }, [])

  // 初始加载时绘制默认图表
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    if (type === 'groove') {
      drawGrooveDiagram(canvas, grooveParams)
    } else {
      drawWeldLayerDiagram(canvas, weldParams)
    }
  }, [type, drawGrooveDiagram, drawWeldLayerDiagram, grooveParams, weldParams])

  // 当参数改变时重新绘制
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    if (type === 'groove') {
      drawGrooveDiagram(canvas, grooveParams)
    }
  }, [grooveParams, type, drawGrooveDiagram])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    if (type === 'weld_layer') {
      drawWeldLayerDiagram(canvas, weldParams)
    }
  }, [weldParams, type, drawWeldLayerDiagram])

  // 生成图表
  const handleGenerate = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    if (type === 'groove') {
      drawGrooveDiagram(canvas, grooveParams)
    } else {
      drawWeldLayerDiagram(canvas, weldParams)
    }

    onGenerate?.(canvas)
    message.success('图表生成成功')
  }

  // 下载图表
  const handleDownload = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const link = document.createElement('a')
    link.href = canvas.toDataURL('image/png')
    link.download = `diagram_${type}_${Date.now()}.png`
    link.click()
    message.success('图表已下载')
  }

  return (
    <Card title={`${type === 'groove' ? '坡口图' : '焊层焊道图'}生成器`}>
      <Row gutter={16}>
        <Col xs={24} sm={12}>
          <Form layout="vertical">
            {type === 'groove' ? (
              <>
                <Form.Item label="坡口类型">
                  <Select
                    value={grooveParams.grooveType}
                    onChange={(value) => setGrooveParams({ ...grooveParams, grooveType: value })}
                  >
                    <Select.Option value="V">V型</Select.Option>
                    <Select.Option value="U">U型</Select.Option>
                    <Select.Option value="J">J型</Select.Option>
                    <Select.Option value="X">X型</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item label="坡口角度 (°)">
                  <InputNumber
                    value={grooveParams.grooveAngle}
                    onChange={(value) => setGrooveParams({ ...grooveParams, grooveAngle: value || 60 })}
                    min={0}
                    max={180}
                  />
                </Form.Item>
                <Form.Item label="根部间隙 (mm)">
                  <InputNumber
                    value={grooveParams.rootGap}
                    onChange={(value) => setGrooveParams({ ...grooveParams, rootGap: value || 2 })}
                    min={0}
                    step={0.5}
                  />
                </Form.Item>
                <Form.Item label="厚度 (mm)">
                  <InputNumber
                    value={grooveParams.thickness}
                    onChange={(value) => setGrooveParams({ ...grooveParams, thickness: value || 10 })}
                    min={1}
                  />
                </Form.Item>
              </>
            ) : (
              <>
                <Form.Item label="焊层数量">
                  <InputNumber
                    value={weldParams.layerCount}
                    onChange={(value) => setWeldParams({ ...weldParams, layerCount: value || 1 })}
                    min={1}
                    max={10}
                  />
                </Form.Item>
                <Form.Item label="每层焊道数">
                  <InputNumber
                    value={weldParams.passPerLayer}
                    onChange={(value) => setWeldParams({ ...weldParams, passPerLayer: value || 1 })}
                    min={1}
                    max={10}
                  />
                </Form.Item>
              </>
            )}
            <Space>
              <Button type="primary" onClick={handleGenerate}>
                生成图表
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                下载
              </Button>
            </Space>
          </Form>
        </Col>
        <Col xs={24} sm={12}>
          <canvas
            ref={canvasRef}
            width={400}
            height={300}
            style={{ border: '1px solid #d9d9d9', borderRadius: '4px' }}
          />
        </Col>
      </Row>
    </Card>
  )
}

export default DiagramGenerator

