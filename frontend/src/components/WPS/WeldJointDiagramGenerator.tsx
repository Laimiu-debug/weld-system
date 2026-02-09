/**
 * 焊接接头示意图生成器
 * 根据参数自动生成焊接接头示意图
 */
import React, { useRef, useEffect } from 'react'
import { Card, Row, Col, Form, InputNumber, Select, Button, Space, message, Divider, AutoComplete } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'

interface WeldJointDiagramGeneratorProps {
  onGenerate?: (canvas: HTMLCanvasElement) => void
}

interface WeldJointParams {
  jointType: 'butt' | 'lap' | 't_joint' | 'corner' | 'edge'  // 接头类型

  // 坡口类型与方向
  grooveType: 'V' | 'U' | 'K' | 'J' | 'X' | 'I'  // 坡口型式
  groovePosition: 'outer' | 'inner'  // 外坡口/内坡口

  // 左侧板材参数
  leftThickness: number  // 左侧板厚 tL (mm)
  leftMaterial?: string  // 左侧母材
  leftGrooveAngle: number  // 左侧坡口角 θL (°)
  leftGrooveDepth: number  // 左侧坡口深度 (mm)
  leftFullPenetration?: boolean  // 左侧是否全焊透

  // 左侧削薄参数
  leftBevel?: boolean  // 左侧是否削薄
  leftBevelPosition?: 'outer' | 'inner'  // 削薄位置：外削边/内削边
  leftBevelLength?: number  // 削薄过渡长度 L (mm)
  leftBevelHeight?: number  // 削薄厚度变化量 H (mm)
  leftBevelCurve?: 'linear' | 'arc' | 'spline'  // 过渡曲线类型

  // 右侧板材参数
  rightThickness: number  // 右侧板厚 tR (mm)
  rightMaterial?: string  // 右侧母材
  rightGrooveAngle: number  // 右侧坡口角 θR (°)
  rightGrooveDepth: number  // 右侧坡口深度 (mm)
  rightFullPenetration?: boolean  // 右侧是否全焊透

  // 右侧削薄参数
  rightBevel?: boolean  // 右侧是否削薄
  rightBevelPosition?: 'outer' | 'inner'  // 削薄位置：外削边/内削边
  rightBevelLength?: number  // 削薄过渡长度 L (mm)
  rightBevelHeight?: number  // 削薄厚度变化量 H (mm)
  rightBevelCurve?: 'linear' | 'arc' | 'spline'  // 过渡曲线类型

  // 根部参数
  bluntEdge: number  // 钝边/根面 t_root (mm)
  rootGap: number  // 根部间隙 g_root (mm)
  topGap?: number  // 顶端间隙 g_top (mm)，可选

  // U型/J型特有参数
  rootRadius?: number  // 根部圆角半径 R_root (mm)
  toeRadius?: number  // 坡口肩部圆角半径 R_toe (mm)

  // 对齐方式与错边
  alignment: 'outer_flush' | 'inner_flush' | 'centerline'  // 对齐基准
  allowedMisalignment?: number  // 允许错边量 e_max (mm)
  actualMisalignment?: number  // 实际错边 e (mm)

  // 背衬与工艺
  backingType?: 'plate' | 'ceramic' | 'gas' | 'none'  // 背衬方式
  weldingSide?: 'single' | 'double'  // 单面/双面焊

  // 焊接参数（保留原有）
  weldWidth: number  // 焊缝宽度 (mm)
  layerCount: number  // 焊层数
  passPerLayer: number  // 每层焊道数
  weldingDirection: 'left_to_right' | 'right_to_left' | 'up_to_down'  // 焊接方向
}

const WeldJointDiagramGenerator: React.FC<WeldJointDiagramGeneratorProps> = ({ onGenerate }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [form] = Form.useForm()
  const [params, setParams] = React.useState<WeldJointParams>({
    jointType: 'butt',

    // 坡口类型与方向
    grooveType: 'V',
    groovePosition: 'outer',

    // 左侧板材参数
    leftThickness: 10,
    leftMaterial: undefined,
    leftGrooveAngle: 30,  // 单侧角度，总角度 = 左 + 右
    leftGrooveDepth: 8,
    leftFullPenetration: false,

    // 左侧削薄参数
    leftBevel: false,
    leftBevelPosition: 'outer',
    leftBevelLength: 15,
    leftBevelHeight: 3,
    leftBevelCurve: 'linear',

    // 右侧板材参数
    rightThickness: 10,
    rightMaterial: undefined,
    rightGrooveAngle: 30,  // 单侧角度
    rightGrooveDepth: 8,
    rightFullPenetration: false,

    // 右侧削薄参数
    rightBevel: false,
    rightBevelPosition: 'outer',
    rightBevelLength: 15,
    rightBevelHeight: 3,
    rightBevelCurve: 'linear',

    // 根部参数
    bluntEdge: 2,
    rootGap: 2,
    topGap: 0,

    // U型/J型特有参数
    rootRadius: 3,
    toeRadius: 2,

    // 对齐方式与错边
    alignment: 'centerline',
    allowedMisalignment: 2,
    actualMisalignment: 0,

    // 背衬与工艺
    backingType: 'none',
    weldingSide: 'single',

    // 焊接参数
    weldWidth: 12,
    layerCount: 3,
    passPerLayer: 2,
    weldingDirection: 'left_to_right'
  })

  // 绘制焊接接头示意图
  const drawWeldJointDiagram = React.useCallback((canvas: HTMLCanvasElement, p: WeldJointParams) => {
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

    // 绘制标题和接头类型
    ctx.fillStyle = '#000'
    ctx.font = 'bold 16px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('焊接接头横截面图', centerX, 30)

    // 绘制接头类型标注
    const jointTypeLabel = {
      butt: '对接接头',
      lap: '搭接接头',
      t_joint: 'T形接头',
      corner: '角接头',
      edge: '边接头'
    }
    const grooveTypeLabel = {
      'V': 'V型',
      'U': 'U型',
      'K': 'K型',
      'J': 'J型',
      'X': 'X型',
      'I': 'I型'
    }
    const grooveSideLabel = {
      'single': '单侧',
      'double': '双侧'
    }
    const groovePositionLabel = {
      'outer': '外坡口',
      'inner': '内坡口'
    }
    ctx.font = '12px Arial'
    ctx.fillText(`${jointTypeLabel[p.jointType]} - ${grooveSideLabel[p.grooveSide]}${grooveTypeLabel[p.grooveType]}${groovePositionLabel[p.groovePosition]}`, centerX, 50)

    // 绘制坡口
    ctx.strokeStyle = '#1890ff'
    ctx.lineWidth = 2
    ctx.fillStyle = 'rgba(24, 144, 255, 0.1)'

    const scale = 8  // 缩放因子
    // 将参数缩放后传递
    const scaledParams = {
      ...p,
      leftThickness: p.leftThickness * scale,
      rightThickness: p.rightThickness * scale,
      leftGrooveDepth: p.leftGrooveDepth * scale,
      rightGrooveDepth: p.rightGrooveDepth * scale,
      rootGap: p.rootGap * scale,
      bluntEdge: p.bluntEdge * scale,
      topGap: (p.topGap || 0) * scale,
      leftBevelLength: (p.leftBevelLength || 0) * scale,
      leftBevelHeight: (p.leftBevelHeight || 0) * scale,
      rightBevelLength: (p.rightBevelLength || 0) * scale,
      rightBevelHeight: (p.rightBevelHeight || 0) * scale,
      rootRadius: (p.rootRadius || 0) * scale,
      toeRadius: (p.toeRadius || 0) * scale
    }

    // 根据接头类型绘制
    switch (p.jointType) {
      case 'butt':
        drawButtJoint(ctx, centerX, centerY, scaledParams)
        break
      case 'lap':
        drawLapJoint(ctx, centerX, centerY, leftThickness, p.grooveType)
        break
      case 't_joint':
        drawTJoint(ctx, centerX, centerY, leftThickness, grooveDepth, angle, p.grooveType)
        break
      case 'corner':
        drawCornerJoint(ctx, centerX, centerY, leftThickness, grooveDepth, angle, p.grooveType)
        break
      case 'edge':
        drawEdgeJoint(ctx, centerX, centerY, leftThickness, grooveDepth, angle, p.grooveType)
        break
    }

    // 绘制参数标注（在图表下方）
    ctx.fillStyle = '#333'
    ctx.font = '11px Arial'
    ctx.textAlign = 'left'
    let labelY = height - 80

    // 绘制参数背景框
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
    // 计算参数框高度
    let paramBoxHeight = 75
    if (p.leftMaterial) paramBoxHeight += 15
    if (p.rightMaterial) paramBoxHeight += 15

    ctx.fillRect(10, labelY - 20, width - 20, paramBoxHeight)
    ctx.strokeStyle = '#999'
    ctx.lineWidth = 1
    ctx.strokeRect(10, labelY - 20, width - 20, paramBoxHeight)

    // 绘制参数文本
    ctx.fillStyle = '#333'
    ctx.font = 'bold 11px Arial'
    ctx.fillText('参数:', 20, labelY)

    ctx.font = '10px Arial'
    ctx.fillStyle = '#555'
    ctx.fillText(`板厚: 左${p.leftThickness}mm 右${p.rightThickness}mm`, 20, labelY + 15)
    ctx.fillText(`坡口角: ${p.grooveAngle}°`, 200, labelY + 15)
    ctx.fillText(`根部间隙: ${p.rootGap}mm`, 20, labelY + 30)
    ctx.fillText(`坡口深: ${p.grooveDepth}mm`, 120, labelY + 30)
    ctx.fillText(`钝边: ${p.bluntEdge}mm`, 220, labelY + 30)

    ctx.fillText(`焊层数: ${p.layerCount}`, 20, labelY + 45)
    ctx.fillText(`每层焊道: ${p.passPerLayer}`, 100, labelY + 45)
    ctx.fillText(`焊缝宽: ${p.weldWidth}mm`, 200, labelY + 45)

    // 绘制母材信息
    let materialLineY = labelY + 60
    if (p.leftMaterial || p.rightMaterial) {
      const leftMat = p.leftMaterial || '未指定'
      const rightMat = p.rightMaterial || '未指定'
      ctx.fillText(`母材: 左侧${leftMat}`, 20, materialLineY)
      materialLineY += 15
      ctx.fillText(`      右侧${rightMat}`, 20, materialLineY)
    }
  }, [])

  // 绘制对接接头 - 横截面图（从侧面看）- 完全重写
  const drawButtJoint = (ctx: CanvasRenderingContext2D, cx: number, cy: number, p: WeldJointParams) => {
    // 横截面图：左右两块板材，中间是坡口
    const plateWidth = 60  // 板材宽度（远离坡口的部分）

    // 解构参数
    const {
      leftThickness: tL,
      rightThickness: tR,
      leftGrooveAngle: θL,
      rightGrooveAngle: θR,
      leftGrooveDepth: dL,
      rightGrooveDepth: dR,
      bluntEdge: t_root,
      rootGap: g_root,
      groovePosition,
      alignment,
      grooveType
    } = p

    // 参数验证：左右独立验证
    // 如果是全焊透，坡口深度等于板厚；否则不超过板厚-1mm
    const validDL = p.leftFullPenetration ? tL : Math.min(dL, tL - 1)
    const validDR = p.rightFullPenetration ? tR : Math.min(dR, tR - 1)
    const validTRoot = Math.min(t_root, Math.min(validDL, validDR) * 0.5)  // 钝边不超过最小坡口深度的一半

    // 计算左右坡口的斜坡宽度（独立计算）
    const θL_rad = (θL * Math.PI) / 180
    const θR_rad = (θR * Math.PI) / 180
    const leftSlopeWidth = (validDL - validTRoot) * Math.tan(θL_rad)
    const rightSlopeWidth = (validDR - validTRoot) * Math.tan(θR_rad)

    // 根据对齐方式计算Y坐标
    // 核心理解：
    // - 外平齐 = 对齐板材的外表面（远离坡口的表面）
    // - 内平齐 = 对齐板材的内表面（靠近坡口的表面）
    // - 外坡口：外表面=上表面，内表面=下表面
    // - 内坡口：外表面=下表面，内表面=上表面
    let leftTopY, leftBottomY, rightTopY, rightBottomY

    if (alignment === 'outer_flush') {
      // 外平齐：对齐外表面（远离坡口的表面）
      if (groovePosition === 'outer') {
        // 外坡口：外表面 = 上表面
        const outerSurfaceY = cy
        leftTopY = outerSurfaceY
        leftBottomY = leftTopY + tL
        rightTopY = outerSurfaceY
        rightBottomY = rightTopY + tR
      } else {
        // 内坡口：外表面 = 下表面
        const outerSurfaceY = cy
        leftBottomY = outerSurfaceY
        leftTopY = leftBottomY - tL
        rightBottomY = outerSurfaceY
        rightTopY = rightBottomY - tR
      }
    } else if (alignment === 'inner_flush') {
      // 内平齐：对齐内表面（靠近坡口的表面）
      if (groovePosition === 'outer') {
        // 外坡口：内表面 = 下表面
        const innerSurfaceY = cy
        leftBottomY = innerSurfaceY
        leftTopY = leftBottomY - tL
        rightBottomY = innerSurfaceY
        rightTopY = rightBottomY - tR
      } else {
        // 内坡口：内表面 = 上表面
        const innerSurfaceY = cy
        leftTopY = innerSurfaceY
        leftBottomY = leftTopY + tL
        rightTopY = innerSurfaceY
        rightBottomY = rightTopY + tR
      }
    } else {
      // 中心线对齐：对齐板材中心线
      const centerY = cy
      leftTopY = centerY - tL / 2
      leftBottomY = centerY + tL / 2
      rightTopY = centerY - tR / 2
      rightBottomY = centerY + tR / 2
    }

    // 计算实际错边量
    const actualMisalignment = alignment === 'outer_flush'
      ? Math.abs(leftBottomY - rightBottomY)
      : alignment === 'inner_flush'
      ? Math.abs(leftTopY - rightTopY)
      : Math.abs((leftTopY + leftBottomY) / 2 - (rightTopY + rightBottomY) / 2)

    // 根据坡口位置（外坡口/内坡口）计算坡口起点和钝边位置
    // 左右独立计算
    let leftGrooveStartY, leftGrooveEndY, leftBluntStartY, leftBluntEndY
    let rightGrooveStartY, rightGrooveEndY, rightBluntStartY, rightBluntEndY

    if (groovePosition === 'outer') {
      // 外坡口：从顶部（上侧）开始向下开
      // 钝边在坡口底部（根部间隙上方）

      // 左侧
      leftGrooveStartY = leftTopY
      leftGrooveEndY = leftTopY + validDL
      leftBluntStartY = leftGrooveEndY - validTRoot
      leftBluntEndY = leftGrooveEndY

      // 右侧
      rightGrooveStartY = rightTopY
      rightGrooveEndY = rightTopY + validDR
      rightBluntStartY = rightGrooveEndY - validTRoot
      rightBluntEndY = rightGrooveEndY
    } else {
      // 内坡口：从底部（下侧）开始向上开
      // 钝边在坡口顶部（根部间隙下方）

      // 左侧
      leftGrooveEndY = leftBottomY
      leftGrooveStartY = leftBottomY - validDL
      leftBluntStartY = leftGrooveStartY
      leftBluntEndY = leftGrooveStartY + validTRoot

      // 右侧
      rightGrooveEndY = rightBottomY
      rightGrooveStartY = rightBottomY - validDR
      rightBluntStartY = rightGrooveStartY
      rightBluntEndY = rightGrooveStartY + validTRoot
    }

    // 根部间隙位置（取左右钝边的平均位置）
    const rootY = groovePosition === 'outer'
      ? (leftBluntEndY + rightBluntEndY) / 2
      : (leftBluntStartY + rightBluntStartY) / 2

    // 绘制左板（支持削边）
    ctx.fillStyle = '#d0d0d0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.beginPath()

    // 左板外侧（远离坡口）
    const leftOuterX = cx - g_root / 2 - leftSlopeWidth - plateWidth

    // 确定削边参数
    const leftBevelLen = (p.leftBevel && p.leftBevelLength) ? p.leftBevelLength * 8 : 0
    const leftBevelH = (p.leftBevel && p.leftBevelHeight) ? p.leftBevelHeight * 8 : 0
    const leftBevelPos = p.leftBevelPosition || 'outer'

    // 左板轮廓（逆时针，从左上角开始）
    if (groovePosition === 'outer') {
      // 外坡口：外表面=上表面，内表面=下表面

      // 1. 左上角
      if (p.leftBevel && leftBevelPos === 'outer') {
        // 外削边：在上表面，板材厚度减少
        ctx.moveTo(leftOuterX, leftTopY + leftBevelH)
      } else {
        ctx.moveTo(leftOuterX, leftTopY)
      }

      // 2. 左下角
      if (p.leftBevel && leftBevelPos === 'inner') {
        // 内削边：在下表面，板材厚度减少
        ctx.lineTo(leftOuterX, leftBottomY - leftBevelH)
      } else {
        ctx.lineTo(leftOuterX, leftBottomY)
      }

      // 3. 削边过渡（如果有内削边）
      if (p.leftBevel && leftBevelPos === 'inner') {
        ctx.lineTo(leftOuterX + leftBevelLen, leftBottomY)
      }

      // 4. 右下角到坡口
      ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftBottomY)

      // 5. 坡口
      ctx.lineTo(cx - g_root / 2, leftBluntEndY)
      ctx.lineTo(cx - g_root / 2, leftBluntStartY)
      ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftGrooveStartY)
      ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftTopY)

      // 6. 削边过渡（如果有外削边）
      if (p.leftBevel && leftBevelPos === 'outer') {
        ctx.lineTo(leftOuterX + leftBevelLen, leftTopY)
      }

    } else {
      // 内坡口：外表面=下表面，内表面=上表面

      // 1. 左上角
      if (p.leftBevel && leftBevelPos === 'inner') {
        // 内削边：在上表面，板材厚度减少
        ctx.moveTo(leftOuterX, leftTopY + leftBevelH)
      } else {
        ctx.moveTo(leftOuterX, leftTopY)
      }

      // 2. 左下角
      if (p.leftBevel && leftBevelPos === 'outer') {
        // 外削边：在下表面，板材厚度减少
        ctx.lineTo(leftOuterX, leftBottomY - leftBevelH)
      } else {
        ctx.lineTo(leftOuterX, leftBottomY)
      }

      // 3. 削边过渡（如果有外削边）
      if (p.leftBevel && leftBevelPos === 'outer') {
        ctx.lineTo(leftOuterX + leftBevelLen, leftBottomY)
      }

      // 4. 右下角到坡口
      ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftBottomY)
      ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftBluntEndY)

      // 5. 坡口
      ctx.lineTo(cx - g_root / 2, leftBluntStartY)
      ctx.lineTo(cx - g_root / 2, leftGrooveEndY)
      ctx.lineTo(cx - g_root / 2 - leftSlopeWidth, leftTopY)

      // 6. 削边过渡（如果有内削边）
      if (p.leftBevel && leftBevelPos === 'inner') {
        ctx.lineTo(leftOuterX + leftBevelLen, leftTopY)
      }
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    // 绘制右板（支持削边）
    ctx.beginPath()

    // 右板外侧（远离坡口）
    const rightOuterX = cx + g_root / 2 + rightSlopeWidth + plateWidth

    // 确定削边参数
    const rightBevelLen = (p.rightBevel && p.rightBevelLength) ? p.rightBevelLength * 8 : 0
    const rightBevelH = (p.rightBevel && p.rightBevelHeight) ? p.rightBevelHeight * 8 : 0
    const rightBevelPos = p.rightBevelPosition || 'outer'

    // 右板轮廓（逆时针，从左上角开始）
    if (groovePosition === 'outer') {
      // 外坡口：外表面=上表面，内表面=下表面

      // 1. 左上角（坡口侧）
      if (p.rightBevel && rightBevelPos === 'outer') {
        // 外削边：在上表面，从削边过渡点开始
        ctx.moveTo(cx + g_root / 2 + rightSlopeWidth + rightBevelLen, rightTopY)
        ctx.lineTo(cx + g_root / 2 + rightSlopeWidth, rightTopY + rightBevelH)
      } else {
        ctx.moveTo(cx + g_root / 2 + rightSlopeWidth, rightTopY)
      }

      // 2. 坡口
      ctx.lineTo(cx + g_root / 2 + rightSlopeWidth, rightGrooveStartY)
      ctx.lineTo(cx + g_root / 2, rightBluntStartY)
      ctx.lineTo(cx + g_root / 2, rightBluntEndY)
      ctx.lineTo(cx + g_root / 2 + rightSlopeWidth, rightBottomY)

      // 3. 削边过渡（如果有内削边）
      if (p.rightBevel && rightBevelPos === 'inner') {
        ctx.lineTo(rightOuterX - rightBevelLen, rightBottomY)
      }

      // 4. 右下角外侧
      if (p.rightBevel && rightBevelPos === 'inner') {
        ctx.lineTo(rightOuterX, rightBottomY - rightBevelH)
      } else {
        ctx.lineTo(rightOuterX, rightBottomY)
      }

      // 5. 右上角外侧
      if (p.rightBevel && rightBevelPos === 'outer') {
        ctx.lineTo(rightOuterX, rightTopY + rightBevelH)
      } else {
        ctx.lineTo(rightOuterX, rightTopY)
      }

    } else {
      // 内坡口：外表面=下表面，内表面=上表面

      // 1. 左上角（坡口侧）
      if (p.rightBevel && rightBevelPos === 'inner') {
        // 内削边：在上表面，从削边过渡点开始
        ctx.moveTo(cx + g_root / 2 + rightSlopeWidth + rightBevelLen, rightTopY)
        ctx.lineTo(cx + g_root / 2 + rightSlopeWidth, rightTopY + rightBevelH)
      } else {
        ctx.moveTo(cx + g_root / 2 + rightSlopeWidth, rightTopY)
      }

      // 2. 坡口
      ctx.lineTo(cx + g_root / 2 + rightSlopeWidth, rightBluntEndY)
      ctx.lineTo(cx + g_root / 2, rightBluntStartY)
      ctx.lineTo(cx + g_root / 2, rightGrooveEndY)
      ctx.lineTo(cx + g_root / 2 + rightSlopeWidth, rightBottomY)

      // 3. 削边过渡（如果有外削边）
      if (p.rightBevel && rightBevelPos === 'outer') {
        ctx.lineTo(rightOuterX - rightBevelLen, rightBottomY)
      }

      // 4. 右下角外侧
      if (p.rightBevel && rightBevelPos === 'outer') {
        ctx.lineTo(rightOuterX, rightBottomY - rightBevelH)
      } else {
        ctx.lineTo(rightOuterX, rightBottomY)
      }

      // 5. 右上角外侧
      if (p.rightBevel && rightBevelPos === 'inner') {
        ctx.lineTo(rightOuterX, rightTopY + rightBevelH)
      } else {
        ctx.lineTo(rightOuterX, rightTopY)
      }
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    // 绘制钝边标注（红色虚线）
    if (grooveType !== 'I') {
      ctx.strokeStyle = '#ff0000'
      ctx.lineWidth = 1.5
      ctx.setLineDash([3, 3])
      ctx.beginPath()

      if (groovePosition === 'outer') {
        // 外坡口：钝边在底部（根部间隙上方）
        const bluntY = (leftBluntStartY + rightBluntStartY) / 2
        ctx.moveTo(cx - g_root / 2 - 10, bluntY)
        ctx.lineTo(cx + g_root / 2 + 10, bluntY)
      } else {
        // 内坡口：钝边在顶部（根部间隙下方）
        const bluntY = (leftBluntEndY + rightBluntEndY) / 2
        ctx.moveTo(cx - g_root / 2 - 10, bluntY)
        ctx.lineTo(cx + g_root / 2 + 10, bluntY)
      }

      ctx.stroke()
      ctx.setLineDash([])  // 恢复实线
    }

    // 绘制根部间隙标注线（指向根部）
    if (grooveType !== 'I') {
      ctx.strokeStyle = '#0000ff'
      ctx.lineWidth = 1.5
      ctx.setLineDash([3, 3])
      ctx.beginPath()
      // 从根部间隙左边到右边的标注线
      ctx.moveTo(cx - g_root / 2, rootY)
      ctx.lineTo(cx - g_root / 2, rootY + 15)
      ctx.moveTo(cx + g_root / 2, rootY)
      ctx.lineTo(cx + g_root / 2, rootY + 15)
      ctx.moveTo(cx - g_root / 2, rootY + 10)
      ctx.lineTo(cx + g_root / 2, rootY + 10)
      ctx.stroke()
      ctx.setLineDash([])

      // 标注根部间隙
      ctx.fillStyle = '#0000ff'
      ctx.font = '10px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(`根部间隙: ${g_root / 8}mm`, cx, rootY + 30)

      // 标注钝边
      ctx.fillStyle = '#ff0000'
      const bluntLabelY = groovePosition === 'outer'
        ? ((leftBluntStartY + rightBluntStartY) / 2) - 5
        : ((leftBluntEndY + rightBluntEndY) / 2) + 15
      ctx.fillText(`钝边: ${validTRoot / 8}mm`, cx, bluntLabelY)

      // 标注左右坡口角度
      ctx.fillStyle = '#666666'
      ctx.font = '9px Arial'
      ctx.textAlign = 'left'
      ctx.fillText(`左角: ${θL}°`, cx - g_root / 2 - leftSlopeWidth - 30, cy)
      ctx.textAlign = 'right'
      ctx.fillText(`右角: ${θR}°`, cx + g_root / 2 + rightSlopeWidth + 30, cy)

      // 如果参数被调整，显示警告
      if (validDL < dL || validDR < dR) {
        ctx.fillStyle = '#ff6600'
        ctx.font = '9px Arial'
        ctx.textAlign = 'center'
        if (validDL < dL) {
          ctx.fillText(`(左侧坡口深度已调整为 ${validDL / 8}mm)`, cx, bluntLabelY + 12)
        }
        if (validDR < dR) {
          ctx.fillText(`(右侧坡口深度已调整为 ${validDR / 8}mm)`, cx, bluntLabelY + 24)
        }
      }
      if (validTRoot < t_root) {
        ctx.fillStyle = '#ff6600'
        ctx.font = '9px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(`(钝边已调整为 ${validTRoot / 8}mm)`, cx, bluntLabelY + 36)
      }
    }
  }

  // 绘制搭接接头 - 横截面图
  const drawLapJoint = (ctx: CanvasRenderingContext2D, cx: number, cy: number, thickness: number, grooveType: string) => {
    const scale = 1
    const plateHeight = thickness * scale
    const overlapWidth = thickness * 1.5

    // 绘制左板
    ctx.fillStyle = '#d0d0d0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.fillRect(cx - overlapWidth / 2 - 40, cy - plateHeight / 2, 40, plateHeight)
    ctx.strokeRect(cx - overlapWidth / 2 - 40, cy - plateHeight / 2, 40, plateHeight)

    // 绘制右板（重叠部分）
    ctx.fillRect(cx - overlapWidth / 2, cy - plateHeight / 2 + 15, overlapWidth, plateHeight - 30)
    ctx.strokeRect(cx - overlapWidth / 2, cy - plateHeight / 2 + 15, overlapWidth, plateHeight - 30)

    // 绘制焊缝区域
    ctx.fillStyle = 'rgba(24, 144, 255, 0.2)'
    ctx.strokeStyle = '#1890ff'
    ctx.lineWidth = 2
    ctx.fillRect(cx - overlapWidth / 2, cy - 8, overlapWidth, 16)
    ctx.strokeRect(cx - overlapWidth / 2, cy - 8, overlapWidth, 16)
  }

  // 绘制T形接头 - 横截面图
  const drawTJoint = (ctx: CanvasRenderingContext2D, cx: number, cy: number, thickness: number, grooveDepth: number, angle: number, grooveType: string) => {
    const scale = 1
    const plateHeight = thickness * scale
    const grooveW = grooveDepth * scale

    // 绘制水平板（左）
    ctx.fillStyle = '#d0d0d0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.fillRect(cx - grooveW / 2 - 60, cy - plateHeight / 2, 60, plateHeight)
    ctx.strokeRect(cx - grooveW / 2 - 60, cy - plateHeight / 2, 60, plateHeight)

    // 绘制竖直板（中间）
    ctx.fillRect(cx - 20, cy - 60, 40, 120)
    ctx.strokeRect(cx - 20, cy - 60, 40, 120)

    // 绘制水平板（右）
    ctx.fillRect(cx + grooveW / 2, cy - plateHeight / 2, 60, plateHeight)
    ctx.strokeRect(cx + grooveW / 2, cy - plateHeight / 2, 60, plateHeight)

    // 绘制焊缝区域
    ctx.fillStyle = 'rgba(24, 144, 255, 0.2)'
    ctx.strokeStyle = '#1890ff'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(cx - 20, cy)
    ctx.lineTo(cx - 30, cy + 20)
    ctx.lineTo(cx + 30, cy + 20)
    ctx.lineTo(cx + 20, cy)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }

  // 绘制角接头 - 横截面图
  const drawCornerJoint = (ctx: CanvasRenderingContext2D, cx: number, cy: number, thickness: number, grooveDepth: number, angle: number, grooveType: string) => {
    const scale = 1
    const plateHeight = thickness * scale
    const grooveW = grooveDepth * scale

    // 绘制左板
    ctx.fillStyle = '#d0d0d0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.fillRect(cx - grooveW / 2 - 60, cy - plateHeight / 2, 60, plateHeight)
    ctx.strokeRect(cx - grooveW / 2 - 60, cy - plateHeight / 2, 60, plateHeight)

    // 绘制右板
    ctx.fillRect(cx + grooveW / 2, cy - plateHeight / 2, 60, plateHeight)
    ctx.strokeRect(cx + grooveW / 2, cy - plateHeight / 2, 60, plateHeight)

    // 绘制焊缝区域（V型）
    ctx.fillStyle = 'rgba(24, 144, 255, 0.2)'
    ctx.strokeStyle = '#1890ff'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(cx - grooveW / 2, cy - plateHeight / 2)
    ctx.lineTo(cx - 5, cy)
    ctx.lineTo(cx + 5, cy)
    ctx.lineTo(cx + grooveW / 2, cy - plateHeight / 2)
    ctx.lineTo(cx + grooveW / 2, cy + plateHeight / 2)
    ctx.lineTo(cx + 5, cy)
    ctx.lineTo(cx - 5, cy)
    ctx.lineTo(cx - grooveW / 2, cy + plateHeight / 2)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }

  // 绘制边接头 - 横截面图
  const drawEdgeJoint = (ctx: CanvasRenderingContext2D, cx: number, cy: number, thickness: number, grooveDepth: number, angle: number, grooveType: string) => {
    const scale = 1
    const plateHeight = thickness * scale
    const plateWidth = thickness * 0.8

    // 绘制左板
    ctx.fillStyle = '#d0d0d0'
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.fillRect(cx - plateWidth - 30, cy - plateHeight / 2, plateWidth, plateHeight)
    ctx.strokeRect(cx - plateWidth - 30, cy - plateHeight / 2, plateWidth, plateHeight)

    // 绘制右板
    ctx.fillRect(cx + 30, cy - plateHeight / 2, plateWidth, plateHeight)
    ctx.strokeRect(cx + 30, cy - plateHeight / 2, plateWidth, plateHeight)

    // 绘制焊缝区域
    ctx.fillStyle = 'rgba(24, 144, 255, 0.2)'
    ctx.strokeStyle = '#1890ff'
    ctx.lineWidth = 2
    ctx.fillRect(cx - 15, cy - plateHeight / 2, 30, plateHeight)
    ctx.strokeRect(cx - 15, cy - plateHeight / 2, 30, plateHeight)
  }

  // 初始加载时绘制默认图表
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    drawWeldJointDiagram(canvas, params)
  }, [params, drawWeldJointDiagram])

  // 生成图表
  const handleGenerate = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    drawWeldJointDiagram(canvas, params)
    onGenerate?.(canvas)
    message.success('焊接接头示意图生成成功')
  }

  // 下载图表
  const handleDownload = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const link = document.createElement('a')
    link.href = canvas.toDataURL('image/png')
    link.download = `weld_joint_diagram_${Date.now()}.png`
    link.click()
    message.success('图表已下载')
  }

  return (
    <Card title="焊接接头示意图生成器">
      <Row gutter={16}>
        <Col xs={24} sm={12}>
          <Form layout="vertical">
            <Form.Item label="接头类型">
              <Select
                value={params.jointType}
                onChange={(value) => setParams({ ...params, jointType: value })}
              >
                <Select.Option value="butt">对接接头</Select.Option>
                <Select.Option value="lap">搭接接头</Select.Option>
                <Select.Option value="t_joint">T形接头</Select.Option>
                <Select.Option value="corner">角接头</Select.Option>
                <Select.Option value="edge">边接头</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item label="坡口类型">
              <Select
                value={params.grooveType}
                onChange={(value) => setParams({ ...params, grooveType: value })}
              >
                <Select.Option value="V">V型</Select.Option>
                <Select.Option value="U">U型</Select.Option>
                <Select.Option value="K">K型</Select.Option>
                <Select.Option value="J">J型</Select.Option>
                <Select.Option value="X">X型</Select.Option>
                <Select.Option value="I">I型（方槽）</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item label="坡口位置">
              <Select
                value={params.groovePosition}
                onChange={(value) => setParams({ ...params, groovePosition: value })}
              >
                <Select.Option value="outer">外坡口（从上侧开）</Select.Option>
                <Select.Option value="inner">内坡口（从下侧开）</Select.Option>
              </Select>
            </Form.Item>

            <Divider>板材参数（左右两侧）</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <h4 style={{ marginBottom: 16, color: '#1890ff' }}>左侧板材</h4>

                <Form.Item label="板厚 (mm)">
              <InputNumber
                value={params.leftThickness}
                onChange={(value) => setParams({ ...params, leftThickness: value || 10 })}
                min={1}
                max={50}
              />
            </Form.Item>

                <Form.Item label="母材">
                  <AutoComplete
                    value={params.leftMaterial}
                    onChange={(value) => setParams({ ...params, leftMaterial: value })}
                    options={[
                      { value: 'Q235' },
                      { value: 'Q345' },
                      { value: '16Mn' },
                      { value: '304不锈钢' },
                      { value: '316不锈钢' },
                      { value: '铝合金' },
                      { value: '铜' }
                    ]}
                    placeholder="选择或输入母材"
                    allowClear
                  />
                </Form.Item>

                <Form.Item label="坡口角度 θL (°)">
                  <InputNumber
                    value={params.leftGrooveAngle}
                    onChange={(value) => setParams({ ...params, leftGrooveAngle: value || 30 })}
                    min={0}
                    max={60}
                    step={5}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item label="全焊透" valuePropName="checked">
                  <input
                    type="checkbox"
                    checked={params.leftFullPenetration || false}
                    onChange={(e) => setParams({ ...params, leftFullPenetration: e.target.checked })}
                  />
                  <span style={{ marginLeft: 8 }}>坡口深度=板厚</span>
                </Form.Item>

                {!params.leftFullPenetration && (
                  <Form.Item
                    label="坡口深度 (mm)"
                    help={params.leftGrooveDepth > params.leftThickness - 1
                      ? `警告：不应超过${params.leftThickness - 1}mm`
                      : undefined}
                    validateStatus={params.leftGrooveDepth > params.leftThickness - 1
                      ? 'warning'
                      : undefined}
                  >
                    <InputNumber
                      value={params.leftGrooveDepth}
                      onChange={(value) => setParams({ ...params, leftGrooveDepth: value || 8 })}
                      min={1}
                      max={params.leftThickness - 1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                )}

                <Form.Item label="削薄" valuePropName="checked">
                  <input
                    type="checkbox"
                    checked={params.leftBevel || false}
                    onChange={(e) => setParams({ ...params, leftBevel: e.target.checked })}
                  />
                  <span style={{ marginLeft: 8 }}>启用削薄</span>
                </Form.Item>

                {params.leftBevel && (
                  <>
                    <Form.Item label="削薄位置">
                      <Select
                        value={params.leftBevelPosition}
                        onChange={(value) => setParams({ ...params, leftBevelPosition: value })}
                      >
                        <Select.Option value="outer">外削边（远离坡口）</Select.Option>
                        <Select.Option value="inner">内削边（靠近坡口）</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item label="削薄长度 L (mm)">
                      <InputNumber
                        value={params.leftBevelLength}
                        onChange={(value) => setParams({ ...params, leftBevelLength: value || 15 })}
                        min={1}
                        max={100}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item label="削薄高度 H (mm)">
                      <InputNumber
                        value={params.leftBevelHeight}
                        onChange={(value) => setParams({ ...params, leftBevelHeight: value || 3 })}
                        min={1}
                        max={params.leftThickness - 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item label="过渡曲线">
                      <Select
                        value={params.leftBevelCurve}
                        onChange={(value) => setParams({ ...params, leftBevelCurve: value })}
                      >
                        <Select.Option value="linear">线性</Select.Option>
                        <Select.Option value="arc">圆弧</Select.Option>
                        <Select.Option value="spline">样条</Select.Option>
                      </Select>
                    </Form.Item>
                  </>
                )}
              </Col>

              <Col span={12}>
                <h4 style={{ marginBottom: 16, color: '#52c41a' }}>右侧板材</h4>

                <Form.Item label="板厚 (mm)">
                  <InputNumber
                    value={params.rightThickness}
                    onChange={(value) => setParams({ ...params, rightThickness: value || 10 })}
                    min={1}
                    max={50}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item label="母材">
                  <AutoComplete
                    value={params.rightMaterial}
                    onChange={(value) => setParams({ ...params, rightMaterial: value })}
                    options={[
                      { value: 'Q235' },
                      { value: 'Q345' },
                      { value: '16Mn' },
                      { value: '304不锈钢' },
                      { value: '316不锈钢' },
                      { value: '铝合金' },
                      { value: '铜' }
                    ]}
                    placeholder="选择或输入母材"
                    allowClear
                  />
                </Form.Item>

                <Form.Item label="坡口角度 θR (°)">
                  <InputNumber
                    value={params.rightGrooveAngle}
                    onChange={(value) => setParams({ ...params, rightGrooveAngle: value || 30 })}
                    min={0}
                    max={60}
                    step={5}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item label="全焊透" valuePropName="checked">
                  <input
                    type="checkbox"
                    checked={params.rightFullPenetration || false}
                    onChange={(e) => setParams({ ...params, rightFullPenetration: e.target.checked })}
                  />
                  <span style={{ marginLeft: 8 }}>坡口深度=板厚</span>
                </Form.Item>

                {!params.rightFullPenetration && (
                  <Form.Item
                    label="坡口深度 (mm)"
                    help={params.rightGrooveDepth > params.rightThickness - 1
                      ? `警告：不应超过${params.rightThickness - 1}mm`
                      : undefined}
                    validateStatus={params.rightGrooveDepth > params.rightThickness - 1
                      ? 'warning'
                      : undefined}
                  >
                    <InputNumber
                      value={params.rightGrooveDepth}
                      onChange={(value) => setParams({ ...params, rightGrooveDepth: value || 8 })}
                      min={1}
                      max={params.rightThickness - 1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                )}

                <Form.Item label="削薄" valuePropName="checked">
                  <input
                    type="checkbox"
                    checked={params.rightBevel || false}
                    onChange={(e) => setParams({ ...params, rightBevel: e.target.checked })}
                  />
                  <span style={{ marginLeft: 8 }}>启用削薄</span>
                </Form.Item>

                {params.rightBevel && (
                  <>
                    <Form.Item label="削薄位置">
                      <Select
                        value={params.rightBevelPosition}
                        onChange={(value) => setParams({ ...params, rightBevelPosition: value })}
                      >
                        <Select.Option value="outer">外削边（远离坡口）</Select.Option>
                        <Select.Option value="inner">内削边（靠近坡口）</Select.Option>
                      </Select>
                    </Form.Item>

                    <Form.Item label="削薄长度 L (mm)">
                      <InputNumber
                        value={params.rightBevelLength}
                        onChange={(value) => setParams({ ...params, rightBevelLength: value || 15 })}
                        min={1}
                        max={100}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item label="削薄高度 H (mm)">
                      <InputNumber
                        value={params.rightBevelHeight}
                        onChange={(value) => setParams({ ...params, rightBevelHeight: value || 3 })}
                        min={1}
                        max={params.rightThickness - 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item label="过渡曲线">
                      <Select
                        value={params.rightBevelCurve}
                        onChange={(value) => setParams({ ...params, rightBevelCurve: value })}
                      >
                        <Select.Option value="linear">线性</Select.Option>
                        <Select.Option value="arc">圆弧</Select.Option>
                        <Select.Option value="spline">样条</Select.Option>
                      </Select>
                    </Form.Item>
                  </>
                )}
              </Col>
            </Row>

            <Divider>根部参数</Divider>

            <Form.Item label="对齐方式">
              <Select
                value={params.alignment}
                onChange={(value) => setParams({ ...params, alignment: value })}
              >
                <Select.Option value="outer_flush">外平齐（上表面对齐）</Select.Option>
                <Select.Option value="centerline">中心线对齐</Select.Option>
                <Select.Option value="inner_flush">内平齐（下表面对齐）</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item label="根部间隙 g_root (mm)">
              <InputNumber
                value={params.rootGap}
                onChange={(value) => setParams({ ...params, rootGap: value || 2 })}
                min={0}
                max={10}
                step={0.5}
              />
            </Form.Item>

            <Form.Item
              label="钝边/根面 t_root (mm)"
              help={params.bluntEdge > Math.min(params.leftGrooveDepth, params.rightGrooveDepth) * 0.5
                ? `警告：钝边不应超过最小坡口深度的一半 (${(Math.min(params.leftGrooveDepth, params.rightGrooveDepth) * 0.5).toFixed(1)}mm)`
                : undefined}
              validateStatus={params.bluntEdge > Math.min(params.leftGrooveDepth, params.rightGrooveDepth) * 0.5
                ? 'warning'
                : undefined}
            >
              <InputNumber
                value={params.bluntEdge}
                onChange={(value) => setParams({ ...params, bluntEdge: value || 2 })}
                min={0}
                max={Math.min(params.leftGrooveDepth, params.rightGrooveDepth) * 0.5}
                step={0.5}
              />
            </Form.Item>

            <Form.Item label="顶端间隙 g_top (mm)">
              <InputNumber
                value={params.topGap}
                onChange={(value) => setParams({ ...params, topGap: value || 0 })}
                min={0}
                max={10}
                step={0.5}
              />
            </Form.Item>

            {(params.grooveType === 'U' || params.grooveType === 'J') && (
              <>
                <Form.Item label="根部圆角半径 R_root (mm)">
                  <InputNumber
                    value={params.rootRadius}
                    onChange={(value) => setParams({ ...params, rootRadius: value || 3 })}
                    min={0}
                    max={10}
                    step={0.5}
                  />
                </Form.Item>

                <Form.Item label="坡口肩部圆角半径 R_toe (mm)">
                  <InputNumber
                    value={params.toeRadius}
                    onChange={(value) => setParams({ ...params, toeRadius: value || 2 })}
                    min={0}
                    max={10}
                    step={0.5}
                  />
                </Form.Item>
              </>
            )}

            <Divider>背衬与工艺</Divider>

            <Form.Item label="背衬方式">
              <Select
                value={params.backingType}
                onChange={(value) => setParams({ ...params, backingType: value })}
              >
                <Select.Option value="none">无背衬</Select.Option>
                <Select.Option value="plate">垫板</Select.Option>
                <Select.Option value="ceramic">陶瓷衬垫</Select.Option>
                <Select.Option value="gas">气体保护</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item label="焊接侧数">
              <Select
                value={params.weldingSide}
                onChange={(value) => setParams({ ...params, weldingSide: value })}
              >
                <Select.Option value="single">单面焊</Select.Option>
                <Select.Option value="double">双面焊</Select.Option>
              </Select>
            </Form.Item>

            <Divider>焊接工艺参数</Divider>

            <Form.Item label="焊缝宽度 (mm)">
              <InputNumber
                value={params.weldWidth}
                onChange={(value) => setParams({ ...params, weldWidth: value || 12 })}
                min={1}
                max={50}
              />
            </Form.Item>

            <Form.Item label="焊层数">
              <InputNumber
                value={params.layerCount}
                onChange={(value) => setParams({ ...params, layerCount: value || 1 })}
                min={1}
                max={10}
              />
            </Form.Item>

            <Form.Item label="每层焊道数">
              <InputNumber
                value={params.passPerLayer}
                onChange={(value) => setParams({ ...params, passPerLayer: value || 1 })}
                min={1}
                max={10}
              />
            </Form.Item>

            <Form.Item label="焊接方向">
              <Select
                value={params.weldingDirection}
                onChange={(value) => setParams({ ...params, weldingDirection: value })}
              >
                <Select.Option value="left_to_right">从左到右</Select.Option>
                <Select.Option value="right_to_left">从右到左</Select.Option>
                <Select.Option value="up_to_down">从上到下</Select.Option>
              </Select>
            </Form.Item>

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
            height={400}
            style={{ border: '1px solid #d9d9d9', borderRadius: '4px', backgroundColor: '#fafafa' }}
          />
        </Col>
      </Row>
    </Card>
  )
}

export default WeldJointDiagramGenerator

