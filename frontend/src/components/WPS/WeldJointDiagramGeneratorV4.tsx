/**
 * 焊接接头示意图生成器 V4
 * 
 * 核心改进：
 * 1. ✅ 支持内外坡口（outer/inner）
 * 2. ✅ 支持左右不同厚度板材
 * 3. ✅ 支持削边（钝边）实现
 * 4. ✅ 支持三种对齐方式（内侧对齐、外侧对齐、中间对齐）
 * 5. ✅ 采用清晰的8点绘制模式
 * 6. ✅ 完整的参数化设计
 * 
 * 绘制逻辑：
 * - 左右板材独立计算8个关键点
 * - 根据对齐方式调整Y坐标偏移
 * - 逆时针绘制板材轮廓
 */

import React, { useRef, useEffect } from 'react'
import { Card, Row, Col, Form, InputNumber, Select, Button, Space, message, Divider } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'

export interface WeldJointParamsV4 {
  // 坡口类型与方向
  grooveType: 'V' | 'U' | 'X' | 'I'
  groovePosition: 'outer' | 'inner'  // 外坡口/内坡口（对于X型，此参数无效）

  // 左侧板材参数
  leftThickness: number  // 板厚 (mm)
  leftGrooveAngle: number  // 坡口角度 (°)，对于U型是圆弧半径
  leftGrooveDepth: number  // 坡口深度 (mm)

  // 左侧削边参数
  leftBevel?: boolean
  leftBevelPosition?: 'outer' | 'inner'  // outer=远离坡口侧, inner=靠近坡口侧
  leftBevelLength?: number  // 削边长度 (mm)
  leftBevelHeight?: number  // 削边高度 (mm)

  // 右侧板材参数
  rightThickness: number
  rightGrooveAngle: number  // 坡口角度 (°)，对于U型是圆弧半径
  rightGrooveDepth: number  // 坡口深度 (mm)

  // 右侧削边参数
  rightBevel?: boolean
  rightBevelPosition?: 'outer' | 'inner'
  rightBevelLength?: number
  rightBevelHeight?: number

  // 根部参数
  bluntEdge: number  // 钝边 (mm)
  rootGap: number  // 根部间隙 (mm)

  // 对齐方式
  alignment: 'inner_flush' | 'outer_flush' | 'centerline'
}

interface Point {
  x: number
  y: number
}

interface WeldJointDiagramGeneratorV4Props {
  onGenerate?: (canvas: HTMLCanvasElement) => void
  initialParams?: Partial<WeldJointParamsV4>
}

const WeldJointDiagramGeneratorV4: React.FC<WeldJointDiagramGeneratorV4Props> = ({
  onGenerate,
  initialParams
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // 默认参数
  const defaultParams: WeldJointParamsV4 = {
    grooveType: 'V',
    groovePosition: 'outer',

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
    alignment: 'centerline'
  }

  // 合并初始参数
  const [params, setParams] = React.useState<WeldJointParamsV4>({
    ...defaultParams,
    ...initialParams
  })

  // 缩放比例
  const SCALE = 6

  useEffect(() => {
    if (canvasRef.current) {
      drawWeldJoint(canvasRef.current, params)
    }
  }, [params])

  /**
   * 计算左侧板材的关键点
   * 坐标系：原点在画布中心，X轴向右，Y轴向下
   */
  const calculateLeftPlatePoints = (
    centerX: number,
    centerY: number,
    p: WeldJointParamsV4,
    yOffset: number  // 根据对齐方式的Y偏移
  ): Point[] => {
    const scale = SCALE

    const thickness = p.leftThickness * scale
    const grooveDepth = p.leftGrooveDepth * scale
    const blunt = p.bluntEdge * scale
    const gap = p.rootGap * scale
    const angle = (p.leftGrooveAngle * Math.PI) / 180

    // 根据坡口类型计算坡口宽度
    let slopeWidth = 0
    if (p.grooveType === 'V' || p.grooveType === 'X') {
      slopeWidth = (grooveDepth - blunt) * Math.tan(angle)
    } else if (p.grooveType === 'U') {
      // U型坡口：使用圆弧，宽度约等于深度的一半
      slopeWidth = grooveDepth * 0.5
    } else if (p.grooveType === 'I') {
      // I型坡口：无坡口角度
      slopeWidth = 0
    }

    const bevelLen = (p.leftBevel && p.leftBevelLength) ? p.leftBevelLength * scale : 0
    const bevelH = (p.leftBevel && p.leftBevelHeight) ? p.leftBevelHeight * scale : 0

    // 板材显示宽度 = 基础宽度 + 坡口宽度 + 削边长度
    const baseWidth = 60  // 基础显示宽度
    const plateWidth = baseWidth + slopeWidth + bevelLen

    const points: Point[] = []

    // 根据坡口位置和对齐方式确定基准Y坐标
    const baseY = centerY + yOffset

    // 根据坡口类型选择绘制方法
    if (p.grooveType === 'V') {
      return calculateLeftPlatePointsV(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    } else if (p.grooveType === 'X') {
      return calculateLeftPlatePointsX(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    } else if (p.grooveType === 'U') {
      return calculateLeftPlatePointsU(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    } else if (p.grooveType === 'I') {
      return calculateLeftPlatePointsI(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    }

    return points
  }

  /**
   * 计算左侧板材的V型坡口点
   */
  const calculateLeftPlatePointsV = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const leftX = centerX - gap / 2 - slopeWidth - plateWidth
    const grooveX = centerX - gap / 2 - slopeWidth
    const rootX = centerX - gap / 2

    if (p.groovePosition === 'outer') {
      // 外坡口：坡口在上方（外侧）
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveBottomY = topY + grooveDepth
      const bluntTopY = grooveBottomY - blunt

      // P0: 左下角
      points.push({ x: leftX, y: bottomY })

      // P1: 右下角（坡口起点下方）- 可能有内削边
      if (p.leftBevel && p.leftBevelPosition === 'inner') {
        points.push({ x: grooveX - bevelLen, y: bottomY })
        points.push({ x: grooveX, y: bottomY - bevelH })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      // P2: 坡口底部（钝边起点）
      points.push({ x: grooveX, y: grooveBottomY })

      // P3: 钝边（水平线）
      points.push({ x: rootX, y: grooveBottomY })
      points.push({ x: rootX, y: bluntTopY })

      // P4: 坡口斜面到顶部 - 可能有外削边
      if (p.leftBevel && p.leftBevelPosition === 'outer') {
        points.push({ x: grooveX, y: topY + bevelH })
        points.push({ x: grooveX - bevelLen, y: topY })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      // P5: 左上角
      points.push({ x: leftX, y: topY })

    } else {
      // 内坡口：坡口在下方（内侧）
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveTopY = bottomY - grooveDepth
      const bluntBottomY = grooveTopY + blunt

      // P0: 左下角（内侧）
      points.push({ x: leftX, y: bottomY })

      // P1: 坡口起点下方 - 可能有内削边
      if (p.leftBevel && p.leftBevelPosition === 'inner') {
        points.push({ x: grooveX - bevelLen, y: bottomY })
        points.push({ x: grooveX, y: bottomY - bevelH })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      // P2: 坡口斜面
      points.push({ x: rootX, y: bluntBottomY })

      // P3: 钝边
      points.push({ x: rootX, y: grooveTopY })

      // P4: 坡口顶部
      points.push({ x: grooveX, y: grooveTopY })

      // P5: 坡口起点上方 - 可能有外削边
      if (p.leftBevel && p.leftBevelPosition === 'outer') {
        points.push({ x: grooveX, y: topY + bevelH })
        points.push({ x: grooveX - bevelLen, y: topY })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      // P6: 左上角（外侧）
      points.push({ x: leftX, y: topY })
    }

    return points
  }

  /**
   * 计算左侧板材的X型坡口点（两侧都有坡口）
   */
  const calculateLeftPlatePointsX = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const leftX = centerX - gap / 2 - slopeWidth - plateWidth
    const grooveX = centerX - gap / 2 - slopeWidth
    const rootX = centerX - gap / 2

    // X型坡口：上下都有坡口
    const topY = baseY
    const bottomY = baseY + thickness
    const centerPlateY = baseY + thickness / 2

    // 上坡口
    const topGrooveBottomY = topY + grooveDepth
    const topBluntTopY = topGrooveBottomY - blunt

    // 下坡口
    const bottomGrooveTopY = bottomY - grooveDepth
    const bottomBluntBottomY = bottomGrooveTopY + blunt

    // P0: 左下角
    points.push({ x: leftX, y: bottomY })

    // P1: 下坡口起点 - 可能有削边
    if (p.leftBevel && p.leftBevelPosition === 'inner') {
      points.push({ x: grooveX - bevelLen, y: bottomY })
      points.push({ x: grooveX, y: bottomY - bevelH })
    } else {
      points.push({ x: grooveX, y: bottomY })
    }

    // P2: 下坡口斜面
    points.push({ x: rootX, y: bottomBluntBottomY })

    // P3: 下钝边
    points.push({ x: rootX, y: bottomGrooveTopY })

    // P4: 中间（如果有间隙）
    points.push({ x: rootX, y: topGrooveBottomY })

    // P5: 上钝边
    points.push({ x: rootX, y: topBluntTopY })

    // P6: 上坡口斜面到顶部 - 可能有削边
    if (p.leftBevel && p.leftBevelPosition === 'outer') {
      points.push({ x: grooveX, y: topY + bevelH })
      points.push({ x: grooveX - bevelLen, y: topY })
    } else {
      points.push({ x: grooveX, y: topY })
    }

    // P7: 左上角
    points.push({ x: leftX, y: topY })

    return points
  }

  /**
   * 计算左侧板材的U型坡口点
   */
  const calculateLeftPlatePointsU = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const leftX = centerX - gap / 2 - slopeWidth - plateWidth
    const grooveX = centerX - gap / 2 - slopeWidth
    const rootX = centerX - gap / 2

    if (p.groovePosition === 'outer') {
      // 外坡口：U型坡口在上方
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveBottomY = topY + grooveDepth
      const bluntTopY = grooveBottomY - blunt

      // P0: 左下角
      points.push({ x: leftX, y: bottomY })

      // P1: 右下角 - 可能有内削边
      if (p.leftBevel && p.leftBevelPosition === 'inner') {
        points.push({ x: grooveX - bevelLen, y: bottomY })
        points.push({ x: grooveX, y: bottomY - bevelH })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      // P2: U型坡口底部（用多个点模拟圆弧）
      points.push({ x: grooveX, y: grooveBottomY })

      // 简化的U型：用直线连接到钝边
      points.push({ x: rootX, y: grooveBottomY })
      points.push({ x: rootX, y: bluntTopY })
      points.push({ x: grooveX, y: topY })

      // P3: 左上角 - 可能有外削边
      if (p.leftBevel && p.leftBevelPosition === 'outer') {
        points.push({ x: grooveX, y: topY + bevelH })
        points.push({ x: grooveX - bevelLen, y: topY })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      points.push({ x: leftX, y: topY })

    } else {
      // 内坡口：U型坡口在下方
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveTopY = bottomY - grooveDepth
      const bluntBottomY = grooveTopY + blunt

      // P0: 左下角
      points.push({ x: leftX, y: bottomY })

      // P1: 右下角 - 可能有内削边
      if (p.leftBevel && p.leftBevelPosition === 'inner') {
        points.push({ x: grooveX - bevelLen, y: bottomY })
        points.push({ x: grooveX, y: bottomY - bevelH })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      // P2: U型坡口（简化）
      points.push({ x: rootX, y: bluntBottomY })
      points.push({ x: rootX, y: grooveTopY })
      points.push({ x: grooveX, y: grooveTopY })
      points.push({ x: grooveX, y: topY })

      // P3: 左上角 - 可能有外削边
      if (p.leftBevel && p.leftBevelPosition === 'outer') {
        points.push({ x: grooveX, y: topY + bevelH })
        points.push({ x: grooveX - bevelLen, y: topY })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      points.push({ x: leftX, y: topY })
    }

    return points
  }

  /**
   * 计算左侧板材的I型坡口点（无坡口）
   */
  const calculateLeftPlatePointsI = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const leftX = centerX - gap / 2 - plateWidth
    const rootX = centerX - gap / 2

    const topY = baseY
    const bottomY = baseY + thickness

    // I型坡口：矩形板材，无坡口角度
    // P0: 左下角
    points.push({ x: leftX, y: bottomY })

    // P1: 右下角 - 可能有内削边
    if (p.leftBevel && p.leftBevelPosition === 'inner') {
      points.push({ x: rootX - bevelLen, y: bottomY })
      points.push({ x: rootX, y: bottomY - bevelH })
    } else {
      points.push({ x: rootX, y: bottomY })
    }

    // P2: 右上角 - 可能有外削边
    if (p.leftBevel && p.leftBevelPosition === 'outer') {
      points.push({ x: rootX, y: topY + bevelH })
      points.push({ x: rootX - bevelLen, y: topY })
    } else {
      points.push({ x: rootX, y: topY })
    }

    // P3: 左上角
    points.push({ x: leftX, y: topY })

    return points
  }

  /**
   * 计算右侧板材的关键点
   */
  const calculateRightPlatePoints = (
    centerX: number,
    centerY: number,
    p: WeldJointParamsV4,
    yOffset: number
  ): Point[] => {
    const scale = SCALE

    const thickness = p.rightThickness * scale
    const grooveDepth = p.rightGrooveDepth * scale
    const blunt = p.bluntEdge * scale
    const gap = p.rootGap * scale
    const angle = (p.rightGrooveAngle * Math.PI) / 180

    // 根据坡口类型计算坡口宽度
    let slopeWidth = 0
    if (p.grooveType === 'V' || p.grooveType === 'X') {
      slopeWidth = (grooveDepth - blunt) * Math.tan(angle)
    } else if (p.grooveType === 'U') {
      slopeWidth = grooveDepth * 0.5
    } else if (p.grooveType === 'I') {
      slopeWidth = 0
    }

    const bevelLen = (p.rightBevel && p.rightBevelLength) ? p.rightBevelLength * scale : 0
    const bevelH = (p.rightBevel && p.rightBevelHeight) ? p.rightBevelHeight * scale : 0

    // 板材显示宽度 = 基础宽度 + 坡口宽度 + 削边长度
    const baseWidth = 60  // 基础显示宽度
    const plateWidth = baseWidth + slopeWidth + bevelLen

    const points: Point[] = []
    const baseY = centerY + yOffset

    // 根据坡口类型选择绘制方法
    if (p.grooveType === 'V') {
      return calculateRightPlatePointsV(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    } else if (p.grooveType === 'X') {
      return calculateRightPlatePointsX(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    } else if (p.grooveType === 'U') {
      return calculateRightPlatePointsU(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    } else if (p.grooveType === 'I') {
      return calculateRightPlatePointsI(centerX, baseY, p, thickness, grooveDepth, blunt, gap, slopeWidth, plateWidth, bevelLen, bevelH, scale)
    }

    return points
  }

  /**
   * 计算右侧板材的V型坡口点
   */
  const calculateRightPlatePointsV = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const rightX = centerX + gap / 2 + slopeWidth + plateWidth
    const grooveX = centerX + gap / 2 + slopeWidth
    const rootX = centerX + gap / 2
    
    if (p.groovePosition === 'outer') {
      // 外坡口
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveBottomY = topY + grooveDepth
      const bluntTopY = grooveBottomY - blunt

      // P0: 钝边底部
      points.push({ x: rootX, y: grooveBottomY })
      points.push({ x: rootX, y: bluntTopY })

      // P1: 坡口斜面到顶部 - 可能有外削边
      if (p.rightBevel && p.rightBevelPosition === 'outer') {
        points.push({ x: grooveX, y: topY + bevelH })
        points.push({ x: grooveX + bevelLen, y: topY })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      // P2: 右上角
      points.push({ x: rightX, y: topY })

      // P3: 右下角
      points.push({ x: rightX, y: bottomY })

      // P4: 坡口起点下方 - 可能有内削边
      if (p.rightBevel && p.rightBevelPosition === 'inner') {
        points.push({ x: grooveX + bevelLen, y: bottomY })
        points.push({ x: grooveX, y: bottomY - bevelH })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      // P5: 坡口底部
      points.push({ x: grooveX, y: grooveBottomY })

    } else {
      // 内坡口
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveTopY = bottomY - grooveDepth
      const bluntBottomY = grooveTopY + blunt

      // P0: 钝边顶部
      points.push({ x: rootX, y: grooveTopY })
      points.push({ x: rootX, y: bluntBottomY })

      // P1: 坡口斜面到底部 - 可能有内削边
      if (p.rightBevel && p.rightBevelPosition === 'inner') {
        points.push({ x: grooveX, y: bottomY - bevelH })
        points.push({ x: grooveX + bevelLen, y: bottomY })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      // P2: 右下角
      points.push({ x: rightX, y: bottomY })

      // P3: 右上角
      points.push({ x: rightX, y: topY })

      // P4: 坡口起点上方 - 可能有外削边
      if (p.rightBevel && p.rightBevelPosition === 'outer') {
        points.push({ x: grooveX + bevelLen, y: topY })
        points.push({ x: grooveX, y: topY + bevelH })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      // P5: 坡口顶部
      points.push({ x: grooveX, y: grooveTopY })
    }

    return points
  }

  /**
   * 计算右侧板材的X型坡口点
   */
  const calculateRightPlatePointsX = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const rightX = centerX + gap / 2 + slopeWidth + plateWidth
    const grooveX = centerX + gap / 2 + slopeWidth
    const rootX = centerX + gap / 2

    // X型坡口：上下都有坡口
    const topY = baseY
    const bottomY = baseY + thickness

    // 上坡口
    const topGrooveBottomY = topY + grooveDepth
    const topBluntTopY = topGrooveBottomY - blunt

    // 下坡口
    const bottomGrooveTopY = bottomY - grooveDepth
    const bottomBluntBottomY = bottomGrooveTopY + blunt

    // P0: 上钝边底部
    points.push({ x: rootX, y: topGrooveBottomY })
    points.push({ x: rootX, y: topBluntTopY })

    // P1: 上坡口斜面到顶部 - 可能有外削边
    if (p.rightBevel && p.rightBevelPosition === 'outer') {
      points.push({ x: grooveX, y: topY + bevelH })
      points.push({ x: grooveX + bevelLen, y: topY })
    } else {
      points.push({ x: grooveX, y: topY })
    }

    // P2: 右上角
    points.push({ x: rightX, y: topY })

    // P3: 右下角
    points.push({ x: rightX, y: bottomY })

    // P4: 下坡口起点 - 可能有内削边
    if (p.rightBevel && p.rightBevelPosition === 'inner') {
      points.push({ x: grooveX + bevelLen, y: bottomY })
      points.push({ x: grooveX, y: bottomY - bevelH })
    } else {
      points.push({ x: grooveX, y: bottomY })
    }

    // P5: 下坡口斜面
    points.push({ x: rootX, y: bottomBluntBottomY })

    // P6: 下钝边
    points.push({ x: rootX, y: bottomGrooveTopY })

    return points
  }

  /**
   * 计算右侧板材的U型坡口点
   */
  const calculateRightPlatePointsU = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const rightX = centerX + gap / 2 + slopeWidth + plateWidth
    const grooveX = centerX + gap / 2 + slopeWidth
    const rootX = centerX + gap / 2

    if (p.groovePosition === 'outer') {
      // 外坡口：U型坡口在上方
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveBottomY = topY + grooveDepth
      const bluntTopY = grooveBottomY - blunt

      // P0: 钝边底部
      points.push({ x: rootX, y: grooveBottomY })
      points.push({ x: rootX, y: bluntTopY })
      points.push({ x: grooveX, y: topY })

      // P1: 右上角 - 可能有外削边
      if (p.rightBevel && p.rightBevelPosition === 'outer') {
        points.push({ x: grooveX, y: topY + bevelH })
        points.push({ x: grooveX + bevelLen, y: topY })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      points.push({ x: rightX, y: topY })

      // P2: 右下角
      points.push({ x: rightX, y: bottomY })

      // P3: 坡口起点 - 可能有内削边
      if (p.rightBevel && p.rightBevelPosition === 'inner') {
        points.push({ x: grooveX + bevelLen, y: bottomY })
        points.push({ x: grooveX, y: bottomY - bevelH })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      points.push({ x: grooveX, y: grooveBottomY })

    } else {
      // 内坡口：U型坡口在下方
      const topY = baseY
      const bottomY = baseY + thickness
      const grooveTopY = bottomY - grooveDepth
      const bluntBottomY = grooveTopY + blunt

      // P0: 钝边顶部
      points.push({ x: rootX, y: grooveTopY })
      points.push({ x: rootX, y: bluntBottomY })
      points.push({ x: grooveX, y: bottomY })

      // P1: 右下角 - 可能有内削边
      if (p.rightBevel && p.rightBevelPosition === 'inner') {
        points.push({ x: grooveX, y: bottomY - bevelH })
        points.push({ x: grooveX + bevelLen, y: bottomY })
      } else {
        points.push({ x: grooveX, y: bottomY })
      }

      points.push({ x: rightX, y: bottomY })

      // P2: 右上角
      points.push({ x: rightX, y: topY })

      // P3: 坡口起点 - 可能有外削边
      if (p.rightBevel && p.rightBevelPosition === 'outer') {
        points.push({ x: grooveX + bevelLen, y: topY })
        points.push({ x: grooveX, y: topY + bevelH })
      } else {
        points.push({ x: grooveX, y: topY })
      }

      points.push({ x: grooveX, y: grooveTopY })
    }

    return points
  }

  /**
   * 计算右侧板材的I型坡口点
   */
  const calculateRightPlatePointsI = (
    centerX: number,
    baseY: number,
    p: WeldJointParamsV4,
    thickness: number,
    grooveDepth: number,
    blunt: number,
    gap: number,
    slopeWidth: number,
    plateWidth: number,
    bevelLen: number,
    bevelH: number,
    scale: number
  ): Point[] => {
    const points: Point[] = []
    const rightX = centerX + gap / 2 + plateWidth
    const rootX = centerX + gap / 2

    const topY = baseY
    const bottomY = baseY + thickness

    // I型坡口：矩形板材，无坡口角度
    // P0: 左上角 - 可能有外削边
    if (p.rightBevel && p.rightBevelPosition === 'outer') {
      points.push({ x: rootX, y: topY + bevelH })
      points.push({ x: rootX + bevelLen, y: topY })
    } else {
      points.push({ x: rootX, y: topY })
    }

    // P1: 右上角
    points.push({ x: rightX, y: topY })

    // P2: 右下角
    points.push({ x: rightX, y: bottomY })

    // P3: 左下角 - 可能有内削边
    if (p.rightBevel && p.rightBevelPosition === 'inner') {
      points.push({ x: rootX + bevelLen, y: bottomY })
      points.push({ x: rootX, y: bottomY - bevelH })
    } else {
      points.push({ x: rootX, y: bottomY })
    }

    return points
  }

  /**
   * 计算Y轴偏移量（根据对齐方式）
   */
  const calculateYOffsets = (p: WeldJointParamsV4): { left: number; right: number } => {
    const leftThickness = p.leftThickness * SCALE
    const rightThickness = p.rightThickness * SCALE

    if (p.alignment === 'centerline') {
      // 中心线对齐：两侧板材中心线对齐
      return {
        left: -leftThickness / 2,
        right: -rightThickness / 2
      }
    } else if (p.alignment === 'outer_flush') {
      // 外侧对齐
      if (p.grooveType === 'X') {
        // X型坡口：外侧=上表面
        return { left: 0, right: 0 }
      } else if (p.groovePosition === 'outer') {
        // 外坡口：外侧=上表面，都从同一Y坐标开始
        return { left: 0, right: 0 }
      } else {
        // 内坡口：外侧=下表面，都从同一Y坐标结束
        return {
          left: -leftThickness,
          right: -rightThickness
        }
      }
    } else {
      // 内侧对齐
      if (p.grooveType === 'X') {
        // X型坡口：内侧=下表面
        return {
          left: -leftThickness,
          right: -rightThickness
        }
      } else if (p.groovePosition === 'outer') {
        // 外坡口：内侧=下表面
        return {
          left: -leftThickness,
          right: -rightThickness
        }
      } else {
        // 内坡口：内侧=上表面
        return { left: 0, right: 0 }
      }
    }
  }

  /**
   * 绘制板材
   */
  const drawPlate = (ctx: CanvasRenderingContext2D, points: Point[], fillColor: string) => {
    if (points.length === 0) return

    ctx.fillStyle = fillColor
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2

    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)

    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y)
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }

  /**
   * 绘制标注
   */
  const drawAnnotations = (
    ctx: CanvasRenderingContext2D,
    centerX: number,
    centerY: number,
    p: WeldJointParamsV4
  ) => {
    const gap = p.rootGap * SCALE

    // 绘制根部间隙标注线
    ctx.strokeStyle = '#0000ff'
    ctx.lineWidth = 1.5
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    ctx.moveTo(centerX - gap / 2, centerY - 40)
    ctx.lineTo(centerX - gap / 2, centerY + 40)
    ctx.moveTo(centerX + gap / 2, centerY - 40)
    ctx.lineTo(centerX + gap / 2, centerY + 40)
    ctx.stroke()
    ctx.setLineDash([])

    // 标注文字
    ctx.fillStyle = '#0000ff'
    ctx.font = '11px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(`根部间隙: ${p.rootGap}mm`, centerX, centerY + 60)

    // 绘制钝边标注
    ctx.fillStyle = '#ff0000'
    ctx.fillText(`钝边: ${p.bluntEdge}mm`, centerX, centerY + 75)

    // 绘制对齐方式标注
    const alignmentText = {
      'centerline': '中心线对齐',
      'outer_flush': '外侧对齐',
      'inner_flush': '内侧对齐'
    }
    ctx.fillStyle = '#666'
    ctx.fillText(`对齐方式: ${alignmentText[p.alignment]}`, centerX, centerY - 60)
  }

  /**
   * 主绘制函数
   */
  const drawWeldJoint = (canvas: HTMLCanvasElement, p: WeldJointParamsV4) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // 绘制标题
    ctx.fillStyle = '#000'
    ctx.font = 'bold 16px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('焊接接头横截面图 V4', canvas.width / 2, 30)

    // 绘制坡口类型和位置
    const grooveTypeLabel = { 'V': 'V型', 'U': 'U型', 'X': 'X型', 'I': 'I型' }
    const groovePositionLabel = { 'outer': '外坡口', 'inner': '内坡口' }
    ctx.font = '12px Arial'
    ctx.fillText(
      `${grooveTypeLabel[p.grooveType]} - ${groovePositionLabel[p.groovePosition]}`,
      canvas.width / 2,
      50
    )

    const centerX = canvas.width / 2
    const centerY = canvas.height / 2

    // 计算Y偏移
    const offsets = calculateYOffsets(p)

    // 计算并绘制左侧板材
    const leftPoints = calculateLeftPlatePoints(centerX, centerY, p, offsets.left)
    drawPlate(ctx, leftPoints, 'rgba(100, 149, 237, 0.4)')

    // 计算并绘制右侧板材
    const rightPoints = calculateRightPlatePoints(centerX, centerY, p, offsets.right)
    drawPlate(ctx, rightPoints, 'rgba(255, 140, 0, 0.4)')

    // 绘制标注
    drawAnnotations(ctx, centerX, centerY, p)

    // 绘制参数信息
    drawParameterInfo(ctx, canvas.width, canvas.height, p)
  }

  /**
   * 绘制参数信息
   */
  const drawParameterInfo = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    p: WeldJointParamsV4
  ) => {
    ctx.fillStyle = '#333'
    ctx.font = '10px Arial'
    ctx.textAlign = 'left'

    let y = height - 100

    // 左侧参数
    ctx.fillStyle = 'rgba(100, 149, 237, 0.8)'
    ctx.fillText(`左侧板厚: ${p.leftThickness}mm`, 20, y)
    y += 15
    ctx.fillText(`左侧坡口角: ${p.leftGrooveAngle}°`, 20, y)
    y += 15
    ctx.fillText(`左侧坡口深: ${p.leftGrooveDepth}mm`, 20, y)

    // 右侧参数
    y = height - 100
    ctx.fillStyle = 'rgba(255, 140, 0, 0.8)'
    ctx.textAlign = 'right'
    ctx.fillText(`右侧板厚: ${p.rightThickness}mm`, width - 20, y)
    y += 15
    ctx.fillText(`右侧坡口角: ${p.rightGrooveAngle}°`, width - 20, y)
    y += 15
    ctx.fillText(`右侧坡口深: ${p.rightGrooveDepth}mm`, width - 20, y)
  }

  // 生成图表
  const handleGenerate = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    drawWeldJoint(canvas, params)
    onGenerate?.(canvas)
    message.success('焊接接头示意图生成成功')
  }

  // 下载图表
  const handleDownload = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const link = document.createElement('a')
    link.href = canvas.toDataURL('image/png')
    link.download = `weld_joint_v4_${Date.now()}.png`
    link.click()
    message.success('图表已下载')
  }

  return (
    <Card title="焊接接头示意图生成器 V4">
      <Row gutter={16}>
        {/* 左侧参数表单 */}
        <Col xs={24} lg={12}>
          <Form layout="vertical">
            {/* 基本参数 */}
            <Divider orientation="left">基本参数</Divider>

            <Form.Item label="坡口类型">
              <Select
                value={params.grooveType}
                onChange={(value) => setParams({ ...params, grooveType: value })}
              >
                <Select.Option value="V">V型坡口</Select.Option>
                <Select.Option value="X">X型坡口</Select.Option>
                <Select.Option value="U">U型坡口</Select.Option>
                <Select.Option value="I">I型坡口（方槽）</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item label="坡口位置" help={params.grooveType === 'X' ? 'X型坡口两侧都有坡口，此选项无效' : ''}>
              <Select
                value={params.groovePosition}
                onChange={(value) => setParams({ ...params, groovePosition: value })}
                disabled={params.grooveType === 'X'}
              >
                <Select.Option value="outer">外坡口（从外侧开坡口）</Select.Option>
                <Select.Option value="inner">内坡口（从内侧开坡口）</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item label="对齐方式">
              <Select
                value={params.alignment}
                onChange={(value) => setParams({ ...params, alignment: value })}
              >
                <Select.Option value="centerline">中心线对齐</Select.Option>
                <Select.Option value="outer_flush">外侧对齐（外表面齐平）</Select.Option>
                <Select.Option value="inner_flush">内侧对齐（内表面齐平）</Select.Option>
              </Select>
            </Form.Item>

            {/* 左侧板材参数 */}
            <Divider orientation="left">左侧板材参数</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="板厚 (mm)">
                  <InputNumber
                    value={params.leftThickness}
                    onChange={(value) => setParams({ ...params, leftThickness: value || 10 })}
                    min={1}
                    max={50}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label={params.grooveType === 'U' ? '坡口参数 (mm)' : '坡口角度 (°)'}
                  help={params.grooveType === 'U' ? 'U型坡口的圆弧参数' : params.grooveType === 'I' ? 'I型坡口无角度' : ''}
                >
                  <InputNumber
                    value={params.leftGrooveAngle}
                    onChange={(value) => setParams({ ...params, leftGrooveAngle: value || 30 })}
                    min={0}
                    max={60}
                    step={5}
                    style={{ width: '100%' }}
                    disabled={params.grooveType === 'I'}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="坡口深度 (mm)">
              <InputNumber
                value={params.leftGrooveDepth}
                onChange={(value) => setParams({ ...params, leftGrooveDepth: value || 8 })}
                min={1}
                max={params.leftThickness}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="启用削边" valuePropName="checked">
              <input
                type="checkbox"
                checked={params.leftBevel || false}
                onChange={(e) => setParams({ ...params, leftBevel: e.target.checked })}
              />
              <span style={{ marginLeft: 8 }}>左侧削边</span>
            </Form.Item>

            {params.leftBevel && (
              <>
                <Form.Item label="削边位置">
                  <Select
                    value={params.leftBevelPosition}
                    onChange={(value) => setParams({ ...params, leftBevelPosition: value })}
                  >
                    <Select.Option value="outer">外削边（板材外侧边界）</Select.Option>
                    <Select.Option value="inner">内削边（板材内侧边界）</Select.Option>
                  </Select>
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="削边长度 (mm)">
                      <InputNumber
                        value={params.leftBevelLength}
                        onChange={(value) => setParams({ ...params, leftBevelLength: value || 15 })}
                        min={1}
                        max={50}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="削边高度 (mm)">
                      <InputNumber
                        value={params.leftBevelHeight}
                        onChange={(value) => setParams({ ...params, leftBevelHeight: value || 2 })}
                        min={1}
                        max={params.leftThickness - 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Col>
                </Row>
              </>
            )}

            {/* 右侧板材参数 */}
            <Divider orientation="left">右侧板材参数</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="板厚 (mm)">
                  <InputNumber
                    value={params.rightThickness}
                    onChange={(value) => setParams({ ...params, rightThickness: value || 10 })}
                    min={1}
                    max={50}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label={params.grooveType === 'U' ? '坡口参数 (mm)' : '坡口角度 (°)'}
                  help={params.grooveType === 'U' ? 'U型坡口的圆弧参数' : params.grooveType === 'I' ? 'I型坡口无角度' : ''}
                >
                  <InputNumber
                    value={params.rightGrooveAngle}
                    onChange={(value) => setParams({ ...params, rightGrooveAngle: value || 30 })}
                    min={0}
                    max={60}
                    step={5}
                    style={{ width: '100%' }}
                    disabled={params.grooveType === 'I'}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="坡口深度 (mm)">
              <InputNumber
                value={params.rightGrooveDepth}
                onChange={(value) => setParams({ ...params, rightGrooveDepth: value || 8 })}
                min={1}
                max={params.rightThickness}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="启用削边" valuePropName="checked">
              <input
                type="checkbox"
                checked={params.rightBevel || false}
                onChange={(e) => setParams({ ...params, rightBevel: e.target.checked })}
              />
              <span style={{ marginLeft: 8 }}>右侧削边</span>
            </Form.Item>

            {params.rightBevel && (
              <>
                <Form.Item label="削边位置">
                  <Select
                    value={params.rightBevelPosition}
                    onChange={(value) => setParams({ ...params, rightBevelPosition: value })}
                  >
                    <Select.Option value="outer">外削边（板材外侧边界）</Select.Option>
                    <Select.Option value="inner">内削边（板材内侧边界）</Select.Option>
                  </Select>
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="削边长度 (mm)">
                      <InputNumber
                        value={params.rightBevelLength}
                        onChange={(value) => setParams({ ...params, rightBevelLength: value || 15 })}
                        min={1}
                        max={50}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="削边高度 (mm)">
                      <InputNumber
                        value={params.rightBevelHeight}
                        onChange={(value) => setParams({ ...params, rightBevelHeight: value || 2 })}
                        min={1}
                        max={params.rightThickness - 1}
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Col>
                </Row>
              </>
            )}

            {/* 根部参数 */}
            <Divider orientation="left">根部参数</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="钝边 (mm)">
                  <InputNumber
                    value={params.bluntEdge}
                    onChange={(value) => setParams({ ...params, bluntEdge: value || 2 })}
                    min={0}
                    max={10}
                    step={0.5}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="根部间隙 (mm)">
                  <InputNumber
                    value={params.rootGap}
                    onChange={(value) => setParams({ ...params, rootGap: value || 2 })}
                    min={0}
                    max={10}
                    step={0.5}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>

            {/* 操作按钮 */}
            <Form.Item>
              <Space>
                <Button type="primary" onClick={handleGenerate}>
                  生成图表
                </Button>
                <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                  下载图表
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Col>

        {/* 右侧画布 */}
        <Col xs={24} lg={12}>
          <canvas
            ref={canvasRef}
            width={600}
            height={500}
            style={{
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              backgroundColor: '#fafafa',
              width: '100%',
              maxWidth: '600px'
            }}
          />
        </Col>
      </Row>
    </Card>
  )
}

export default WeldJointDiagramGeneratorV4
