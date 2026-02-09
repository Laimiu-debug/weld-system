/**
 * 焊接接头示意图生成器 V2
 * 
 * 新的绘制逻辑：
 * 1. 不考虑上下对齐问题
 * 2. 左右板材独立绘制
 * 3. 内外坡口绘制顺序清晰
 * 4. 支持削边处理
 */

import React from 'react'
import { Button, Card, Space, message } from 'antd'

interface WeldJointParamsV2 {
  // 坡口类型与方向
  grooveType: 'V' | 'U' | 'K' | 'J' | 'X' | 'I'  // 坡口型式
  groovePosition: 'outer' | 'inner'  // 外坡口/内坡口

  // 左侧板材参数
  leftThickness: number  // 左侧板厚 (mm)
  leftGrooveAngle: number  // 左侧坡口角 (°)
  leftGrooveDepth: number  // 左侧坡口深度 (mm)
  
  // 左侧削边参数
  leftBevel?: boolean  // 是否削边
  leftBevelPosition?: 'outer' | 'inner'  // 削边位置
  leftBevelLength?: number  // 削边长度 (mm)
  leftBevelHeight?: number  // 削边高度 (mm)

  // 右侧板材参数
  rightThickness: number  // 右侧板厚 (mm)
  rightGrooveAngle: number  // 右侧坡口角 (°)
  rightGrooveDepth: number  // 右侧坡口深度 (mm)
  
  // 右侧削边参数
  rightBevel?: boolean
  rightBevelPosition?: 'outer' | 'inner'
  rightBevelLength?: number
  rightBevelHeight?: number

  // 根部参数
  bluntEdge: number  // 钝边 (mm)
  rootGap: number  // 根部间隙 (mm)
}

interface Props {
  params: WeldJointParamsV2
  width?: number
  height?: number
}

const WeldJointDiagramGeneratorV2: React.FC<Props> = ({ 
  params, 
  width = 800, 
  height = 600 
}) => {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)

  React.useEffect(() => {
    if (canvasRef.current) {
      drawWeldJoint(canvasRef.current, params)
    }
  }, [params])

  // 绘制焊接接头
  const drawWeldJoint = (canvas: HTMLCanvasElement, p: WeldJointParamsV2) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // 绘制边框
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 1
    ctx.strokeRect(0, 0, canvas.width, canvas.height)

    // 绘制标题
    ctx.fillStyle = '#000'
    ctx.font = 'bold 16px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('焊接接头横截面图 V2', canvas.width / 2, 30)

    // 绘制接头
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    drawButtJointV2(ctx, centerX, centerY, p)
  }

  // 绘制对接接头 - 新逻辑
  const drawButtJointV2 = (
    ctx: CanvasRenderingContext2D, 
    cx: number, 
    cy: number, 
    p: WeldJointParamsV2
  ) => {
    const scale = 8  // 缩放比例
    const plateWidth = 60  // 板材宽度

    // 缩放参数
    const tL = p.leftThickness * scale
    const tR = p.rightThickness * scale
    const dL = p.leftGrooveDepth * scale
    const dR = p.rightGrooveDepth * scale
    const blunt = p.bluntEdge * scale
    const gap = p.rootGap * scale

    // 计算坡口斜坡宽度
    const θL = (p.leftGrooveAngle * Math.PI) / 180
    const θR = (p.rightGrooveAngle * Math.PI) / 180
    const leftSlopeWidth = (dL - blunt) * Math.tan(θL)
    const rightSlopeWidth = (dR - blunt) * Math.tan(θR)

    // 削边参数
    const leftBevelLen = (p.leftBevel && p.leftBevelLength) ? p.leftBevelLength * scale : 0
    const leftBevelH = (p.leftBevel && p.leftBevelHeight) ? p.leftBevelHeight * scale : 0
    const rightBevelLen = (p.rightBevel && p.rightBevelLength) ? p.rightBevelLength * scale : 0
    const rightBevelH = (p.rightBevel && p.rightBevelHeight) ? p.rightBevelHeight * scale : 0

    // 绘制左侧板材
    drawLeftPlate(ctx, cx, cy, {
      thickness: tL,
      grooveDepth: dL,
      bluntEdge: blunt,
      rootGap: gap,
      slopeWidth: leftSlopeWidth,
      plateWidth,
      groovePosition: p.groovePosition,
      bevel: p.leftBevel,
      bevelPosition: p.leftBevelPosition,
      bevelLength: leftBevelLen,
      bevelHeight: leftBevelH
    })

    // 计算右侧板材起始点
    const rightStartPoint = calculateRightStartPoint(cx, cy, {
      leftThickness: tL,
      leftGrooveDepth: dL,
      bluntEdge: blunt,
      rootGap: gap,
      groovePosition: p.groovePosition
    })

    // 绘制右侧板材
    drawRightPlate(ctx, rightStartPoint.x, rightStartPoint.y, {
      thickness: tR,
      grooveDepth: dR,
      bluntEdge: blunt,
      rootGap: gap,
      slopeWidth: rightSlopeWidth,
      plateWidth,
      groovePosition: p.groovePosition,
      bevel: p.rightBevel,
      bevelPosition: p.rightBevelPosition,
      bevelLength: rightBevelLen,
      bevelHeight: rightBevelH
    })

    // 绘制标注
    drawAnnotations(ctx, cx, cy, p, scale)
  }

  // 绘制左侧板材
  const drawLeftPlate = (
    ctx: CanvasRenderingContext2D,
    cx: number,
    cy: number,
    params: {
      thickness: number
      grooveDepth: number
      bluntEdge: number
      rootGap: number
      slopeWidth: number
      plateWidth: number
      groovePosition: 'outer' | 'inner'
      bevel?: boolean
      bevelPosition?: 'outer' | 'inner'
      bevelLength: number
      bevelHeight: number
    }
  ) => {
    const {
      thickness, grooveDepth, bluntEdge, rootGap, slopeWidth, plateWidth,
      groovePosition, bevel, bevelPosition, bevelLength, bevelHeight
    } = params

    ctx.fillStyle = '#d0d0d0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.beginPath()

    // 左侧板材的左下角起始点
    const leftEdgeX = cx - rootGap / 2 - slopeWidth - plateWidth
    const bottomY = cy + thickness / 2

    // 1. 从左下角开始
    ctx.moveTo(leftEdgeX, bottomY)

    // 2. 绘制下边界，判断下边界是否有削边
    // 下边界削边：bevelPosition === 'inner'（向上削，板材变薄）
    if (bevel && bevelPosition === 'inner') {
      // 有下边界削边：从左侧端点开始，向右绘制一段，然后削边斜线到根部
      const bevelEndX = leftEdgeX + bevelLength
      const bevelEndY = bottomY + bevelHeight
      ctx.lineTo(bevelEndX, bevelEndY)  // 削边斜线起点
      ctx.lineTo(cx - rootGap / 2 - slopeWidth, bottomY)  // 削边斜线到根部
    } else {
      // 没有削边：直接向右绘制下边界直到根部
      ctx.lineTo(cx - rootGap / 2 - slopeWidth, bottomY)
    }

    // 3. 到达根部，判断内外坡口
    if (groovePosition === 'inner') {
      // 内坡口：先绘制坡口，再绘制钝边
      const grooveTopY = bottomY - grooveDepth
      const bluntTopY = grooveTopY + bluntEdge

      // 绘制坡口斜面
      ctx.lineTo(cx - rootGap / 2 - slopeWidth, bluntTopY)
      // 绘制钝边
      ctx.lineTo(cx - rootGap / 2, bluntTopY)
      ctx.lineTo(cx - rootGap / 2, grooveTopY)
    } else {
      // 外坡口：先绘制钝边，再绘制坡口
      const bluntStartY = bottomY - bluntEdge
      const grooveTopY = bottomY - grooveDepth

      // 绘制钝边
      ctx.lineTo(cx - rootGap / 2, bottomY)
      ctx.lineTo(cx - rootGap / 2, bluntStartY)
      // 绘制坡口斜面
      ctx.lineTo(cx - rootGap / 2 - slopeWidth, grooveTopY)
    }

    // 4. 绘制上边界，从钝边终点或坡口斜面终点开始
    let currentX, currentY

    if (groovePosition === 'inner') {
      // 内坡口：从钝边终点开始 (cx - rootGap / 2, grooveTopY)
      currentX = cx - rootGap / 2
      currentY = bottomY - grooveDepth
    } else {
      // 外坡口：从坡口斜面终点开始 (cx - rootGap / 2 - slopeWidth, grooveTopY)
      currentX = cx - rootGap / 2 - slopeWidth
      currentY = bottomY - grooveDepth
    }

    // 上边界削边：bevelPosition === 'outer'（向上削，板材变薄）
    if (bevel && bevelPosition === 'outer') {
      // 有上边界削边：从当前点开始，绘制削边斜线
      const bevelEndX = currentX - bevelLength
      const bevelEndY = currentY - bevelHeight
      ctx.lineTo(bevelEndX, bevelEndY)  // 削边斜线终点

      // 从削边终点向左绘制上边界，板材宽度根据削边宽度动态调整
      const dynamicPlateWidth = Math.max(plateWidth, bevelLength + 20) // 至少比削边长度多20mm
      ctx.lineTo(bevelEndX - dynamicPlateWidth, bevelEndY)

      // 向下绘制左边界到下边界
      ctx.lineTo(bevelEndX - dynamicPlateWidth, bottomY)

      // 向右绘制到起始点，闭合曲线
      ctx.lineTo(cx - rootGap / 2 - slopeWidth, bottomY)
    } else {
      // 没有削边：直接向左延伸绘制上边界
      ctx.lineTo(currentX - plateWidth, currentY)  // 从当前点向左延伸
      ctx.lineTo(currentX - plateWidth, bottomY)  // 向下到左下角
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }

  // 计算右侧板材起始点
  const calculateRightStartPoint = (
    cx: number,
    cy: number,
    params: {
      leftThickness: number
      leftGrooveDepth: number
      bluntEdge: number
      rootGap: number
      groovePosition: 'outer' | 'inner'
    }
  ) => {
    const { leftThickness, leftGrooveDepth, bluntEdge, rootGap, groovePosition } = params

    // Y坐标：从左侧板钝边的终点获取（基于画布中心cy）
    let y: number
    const leftBottomY = cy + leftThickness / 2

    if (groovePosition === 'inner') {
      // 内坡口：钝边在下方，终点 = 底部 - 坡口深度 + 钝边
      y = leftBottomY - leftGrooveDepth + bluntEdge
    } else {
      // 外坡口：钝边在下方，终点 = 底部 - 钝边
      y = leftBottomY - bluntEdge
    }

    // X坐标：左侧板钝边终点的X坐标 + 根部间隙
    const x = cx + rootGap / 2

    return { x, y }
  }

  // 绘制右侧板材
  const drawRightPlate = (
    ctx: CanvasRenderingContext2D,
    startX: number,
    startY: number,
    params: {
      thickness: number
      grooveDepth: number
      bluntEdge: number
      rootGap: number
      slopeWidth: number
      plateWidth: number
      groovePosition: 'outer' | 'inner'
      bevel?: boolean
      bevelPosition?: 'outer' | 'inner'
      bevelLength: number
      bevelHeight: number
    }
  ) => {
    const {
      thickness, grooveDepth, bluntEdge, rootGap, slopeWidth, plateWidth,
      groovePosition, bevel, bevelPosition, bevelLength, bevelHeight
    } = params

    ctx.fillStyle = '#b0b0b0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.beginPath()

    // 右侧板材从钝边终点开始 (startX, startY)
    ctx.moveTo(startX, startY)

    const rightEdgeX = startX + slopeWidth + plateWidth

    if (groovePosition === 'inner') {
      // 内坡口
      // 向上：直接判断是否有削边
      const topY = startY - bluntEdge

      // 绘制钝边
      ctx.lineTo(startX, topY)

      // 判断上边界是否有削边（从当前点向右削边）
      if (bevel && bevelPosition === 'outer') {
        // 有上边界削边：从当前点开始，绘制削边斜线
        const bevelEndX = startX + bevelLength
        const bevelEndY = topY - bevelHeight
        ctx.lineTo(bevelEndX, bevelEndY)  // 削边斜线终点
        ctx.lineTo(rightEdgeX, topY)  // 继续向右到右侧端点
      } else {
        // 没有削边
        ctx.lineTo(rightEdgeX, topY)
      }

      // 向下：到达下边界 → 判断下边界削边 → 绘制坡口斜面 → 绘制钝边
      const bottomY = startY + thickness - grooveDepth

      // 判断下边界削边（从右侧端点向内削边）
      if (bevel && bevelPosition === 'inner') {
        // 有下边界削边：从右侧端点开始，向左绘制一段，然后削边斜线到坡口边缘
        const bevelEndX = rightEdgeX - bevelLength
        const bevelEndY = bottomY + bevelHeight
        ctx.lineTo(bevelEndX, bevelEndY)  // 削边斜线起点
        ctx.lineTo(startX + slopeWidth, bottomY)  // 削边斜线到坡口边缘
      } else {
        // 没有削边
        ctx.lineTo(rightEdgeX, bottomY)
        ctx.lineTo(startX + slopeWidth, bottomY)
      }

      // 绘制坡口斜面
      ctx.lineTo(startX, startY)

    } else {
      // 外坡口
      // 向上：绘制坡口斜面
      const topY = startY - thickness + bluntEdge

      // 绘制坡口斜面
      ctx.lineTo(startX + slopeWidth, topY)

      // 判断上边界是否有削边（从当前点向右削边）
      if (bevel && bevelPosition === 'outer') {
        // 有上边界削边：从当前点开始，绘制削边斜线
        const bevelEndX = startX + slopeWidth + bevelLength
        const bevelEndY = topY - bevelHeight
        ctx.lineTo(bevelEndX, bevelEndY)  // 削边斜线终点
        ctx.lineTo(rightEdgeX, topY)  // 继续向右到右侧端点
      } else {
        // 没有削边
        ctx.lineTo(rightEdgeX, topY)
      }

      // 向下：绘制钝边
      const bottomY = startY + bluntEdge

      // 绘制钝边
      ctx.lineTo(rightEdgeX, bottomY)

      // 判断下边界削边（从右侧端点向内削边）
      if (bevel && bevelPosition === 'inner') {
        // 有下边界削边：从右侧端点开始，向左绘制一段，然后削边斜线到起始点
        const bevelEndX = rightEdgeX - bevelLength
        const bevelEndY = bottomY + bevelHeight
        ctx.lineTo(bevelEndX, bevelEndY)  // 削边斜线起点
        ctx.lineTo(startX, bottomY)  // 削边斜线到起始点
      } else {
        // 没有削边
        ctx.lineTo(startX, bottomY)
      }
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }

  // 绘制标注
  const drawAnnotations = (
    ctx: CanvasRenderingContext2D,
    cx: number,
    cy: number,
    p: WeldJointParamsV2,
    scale: number
  ) => {
    ctx.font = '12px Arial'
    ctx.fillStyle = '#000'
    ctx.textAlign = 'left'

    let labelY = cy + p.leftThickness * scale / 2 + 80

    // 坡口类型
    ctx.fillText(`坡口类型: ${p.grooveType}型`, 20, labelY)
    labelY += 20

    // 坡口位置
    ctx.fillText(`坡口位置: ${p.groovePosition === 'outer' ? '外坡口' : '内坡口'}`, 20, labelY)
    labelY += 20

    // 左侧参数
    ctx.fillText(`左侧板厚: ${p.leftThickness}mm`, 20, labelY)
    labelY += 15
    ctx.fillText(`左侧坡口角: ${p.leftGrooveAngle}°`, 20, labelY)
    labelY += 15
    ctx.fillText(`左侧坡口深度: ${p.leftGrooveDepth}mm`, 20, labelY)
    labelY += 20

    // 右侧参数
    ctx.fillText(`右侧板厚: ${p.rightThickness}mm`, 20, labelY)
    labelY += 15
    ctx.fillText(`右侧坡口角: ${p.rightGrooveAngle}°`, 20, labelY)
    labelY += 15
    ctx.fillText(`右侧坡口深度: ${p.rightGrooveDepth}mm`, 20, labelY)
    labelY += 20

    // 根部参数
    ctx.fillText(`钝边: ${p.bluntEdge}mm`, 20, labelY)
    labelY += 15
    ctx.fillText(`根部间隙: ${p.rootGap}mm`, 20, labelY)

    // 绘制钝边标注线（红色虚线）
    ctx.strokeStyle = '#ff0000'
    ctx.lineWidth = 1.5
    ctx.setLineDash([3, 3])
    ctx.beginPath()

    const blunt = p.bluntEdge * scale
    const thickness = p.leftThickness * scale

    if (p.groovePosition === 'inner') {
      // 内坡口：钝边在上方
      const bluntY = cy + thickness / 2 - p.leftGrooveDepth * scale + blunt
      ctx.moveTo(cx - 50, bluntY)
      ctx.lineTo(cx + 50, bluntY)
    } else {
      // 外坡口：钝边在下方
      const bluntY = cy + thickness / 2 - blunt
      ctx.moveTo(cx - 50, bluntY)
      ctx.lineTo(cx + 50, bluntY)
    }

    ctx.stroke()
    ctx.setLineDash([])  // 恢复实线

    // 绘制根部间隙标注
    ctx.strokeStyle = '#0000ff'
    ctx.lineWidth = 1
    ctx.setLineDash([2, 2])
    ctx.beginPath()
    ctx.moveTo(cx - p.rootGap * scale / 2, cy - 30)
    ctx.lineTo(cx - p.rootGap * scale / 2, cy + 30)
    ctx.moveTo(cx + p.rootGap * scale / 2, cy - 30)
    ctx.lineTo(cx + p.rootGap * scale / 2, cy + 30)
    ctx.stroke()
    ctx.setLineDash([])
  }

  return (
    <Card title="焊接接头示意图生成器 V2">
      <Space direction="vertical" style={{ width: '100%' }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          style={{ border: '1px solid #d9d9d9', width: '100%' }}
        />
      </Space>
    </Card>
  )
}

export default WeldJointDiagramGeneratorV2

