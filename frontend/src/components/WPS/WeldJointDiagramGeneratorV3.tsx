import React, { useEffect, useRef } from 'react'

/**
 * 焊接接头示意图生成器 V3
 * 基于8点逆时针绘制模式
 *
 * 左侧板材8个点（逆时针）：
 * A - 左下角原点 (0, 0)
 * B - 下边界削边起始点
 * C - 下边界削边终止点 = 下坡口起始点
 * D - 下坡口终止点 = 钝边起始点
 * E - 钝边终止点 = 上坡口起始点
 * F - 上坡口终止点 = 上边界削边起始点
 * G - 上边界削边终止点
 * H - 左上角
 *
 * 线段分类：
 * - 直线段：AB(下边界), DE(钝边), GH(上边界), HA(左侧竖直边)
 * - 削边段：BC(下削边), FG(上削边)
 * - 坡口段：CD(下坡口), EF(上坡口) - 可以是直线(V)、圆弧(U/J)
 */

export interface WeldJointParamsV3 {
  grooveType: 'V' | 'U' | 'J' | 'X'
  groovePosition: 'outer' | 'inner'

  leftThickness: number
  leftGrooveAngle: number
  // leftGrooveDepth: number  // 移除：默认全焊透
  leftBevel?: boolean
  leftBevelPosition?: 'outer' | 'inner'
  leftBevelLength?: number
  leftBevelHeight?: number

  rightThickness: number
  rightGrooveAngle: number
  // rightGrooveDepth: number  // 移除：默认全焊透
  rightBevel?: boolean
  rightBevelPosition?: 'outer' | 'inner'
  rightBevelLength?: number
  rightBevelHeight?: number

  bluntEdge: number
  rootGap: number
}

interface WeldJointDiagramGeneratorV3Props {
  params: WeldJointParamsV3
  width?: number
  height?: number
}

const WeldJointDiagramGeneratorV3: React.FC<WeldJointDiagramGeneratorV3Props> = ({
  params,
  width = 800,
  height = 400
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [leftPoints, setLeftPoints] = React.useState<{[key: string]: {x: number, y: number}}>({})
  const [rightPoints, setRightPoints] = React.useState<{[key: string]: {x: number, y: number}}>({})

  // 辅助函数：绘制坐标系
  const drawCoordinateSystem = (
    ctx: CanvasRenderingContext2D,
    originX: number,
    originY: number,
    width: number,
    height: number
  ) => {
    ctx.strokeStyle = '#ddd'
    ctx.lineWidth = 1

    // 绘制坐标轴
    ctx.beginPath()
    // X轴
    ctx.moveTo(0, originY)
    ctx.lineTo(width, originY)
    // Y轴
    ctx.moveTo(originX, 0)
    ctx.lineTo(originX, height)
    ctx.stroke()

    // 标记原点
    ctx.fillStyle = '#666'
    ctx.font = '12px Arial'
    ctx.fillText('O', originX - 15, originY + 15)
  }

  // 左侧板材绘制函数
  const drawLeftPlate = (
    ctx: CanvasRenderingContext2D,
    originX: number,
    originY: number,
    config: {
      thickness: number
      grooveDepth: number
      bluntEdge: number
      rootGap: number
      slopeWidth: number
      plateWidth: number
      groovePosition: 'outer' | 'inner'
      grooveType: 'V' | 'U' | 'J' | 'X'
      grooveAngle: number
      bevel?: boolean
      bevelPosition?: 'outer' | 'inner'
      bevelLength: number
      bevelHeight: number
    }
  ) => {
    const {
      thickness, grooveDepth, bluntEdge, slopeWidth, plateWidth,
      groovePosition, grooveType, grooveAngle, bevel, bevelPosition, bevelLength, bevelHeight
    } = config

    // 左侧板材的8个点（逆时针）：
    const points: {[key: string]: {x: number, y: number}} = {}

    // A点：原点
    points.A = {x: originX, y: originY}

    // B点：下边界削边起始点
    if (bevel && bevelPosition === 'inner') {
      points.B = {x: originX + bevelLength, y: originY}
    } else {
      points.B = points.A
    }

    // C点：下坡口起始点
    points.C = {x: originX + plateWidth, y: originY}

    // D点：下坡口终止点（钝边起始点）
    const lowerGrooveHeight = grooveDepth
    if (groovePosition === 'inner') {
      // 内坡口：CD为斜线
      points.D = {x: originX + plateWidth + slopeWidth, y: originY + lowerGrooveHeight}
    } else {
      // 外坡口：CD为竖直线
      points.D = {x: originX + plateWidth, y: originY + lowerGrooveHeight}
    }

    // E点：上坡口起始点（钝边终止点）
    const upperGrooveHeight = grooveDepth
    if (bluntEdge === 0) {
      // 钝边为0时，D点和E点重合
      points.E = points.D
    } else {
      points.E = {x: points.D.x + bluntEdge, y: points.D.y}
    }

    // F点：上坡口终止点
    if (groovePosition === 'inner') {
      // 内坡口：EF为竖直线
      points.F = {x: points.E.x, y: originY + upperGrooveHeight}
    } else {
      // 外坡口：EF为斜线
      points.F = {x: points.E.x + slopeWidth, y: originY + upperGrooveHeight}
    }

    // G点：上边界削边终止点
    if (bevel && bevelPosition === 'inner') {
      points.G = {x: originX + plateWidth + bevelLength, y: originY + thickness}
    } else {
      points.G = {x: originX + plateWidth, y: originY + thickness}
    }

    // H点：左上角
    points.H = {x: originX, y: originY + thickness}

    // 绘制左侧板材
    ctx.fillStyle = 'rgba(100, 149, 237, 0.3)'
    ctx.strokeStyle = '#333'
    ctx.lineWidth = 2

    ctx.beginPath()
    ctx.moveTo(points.A.x, points.A.y)

    // AB：下边界
    ctx.lineTo(points.B.x, points.B.y)

    // BC：下削边
    ctx.lineTo(points.C.x, points.C.y)

    // CD：下坡口
    if (grooveType === 'V' || grooveType === 'X') {
      ctx.lineTo(points.D.x, points.D.y)
    } else if (grooveType === 'U' || grooveType === 'J') {
      // U型坡口用圆弧
      const centerX = points.C.x + slopeWidth / 2
      const centerY = points.C.y + grooveDepth
      const radius = grooveDepth
      ctx.arcTo(centerX + radius, centerY, centerX + radius, points.D.y, radius)
    }

    // DE：钝边
    ctx.lineTo(points.E.x, points.E.y)

    // EF：上坡口
    if (grooveType === 'V' || grooveType === 'X') {
      ctx.lineTo(points.F.x, points.F.y)
    } else if (grooveType === 'U' || grooveType === 'J') {
      // U型坡口用圆弧
      const centerX = points.E.x + slopeWidth / 2
      const centerY = points.E.y - grooveDepth
      const radius = grooveDepth
      ctx.arcTo(centerX + radius, centerY, centerX + radius, points.F.y, radius)
    }

    // FG：上削边
    ctx.lineTo(points.G.x, points.G.y)

    // GH：上边界
    ctx.lineTo(points.H.x, points.H.y)

    // HA：左侧竖直边
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    return points
  }

  // 右侧板材绘制函数
  const drawRightPlateDirect = (
    ctx: CanvasRenderingContext2D,
    originX: number,
    originY: number,
    config: {
      thickness: number
      grooveDepth: number
      bluntEdge: number
      rootGap: number
      slopeWidth: number
      plateWidth: number
      groovePosition: 'outer' | 'inner'
      grooveType: 'V' | 'U' | 'J' | 'X'
      grooveAngle: number
      bevel?: boolean
      bevelPosition?: 'outer' | 'inner'
      bevelLength: number
      bevelHeight: number
    },
    leftDPoint: {x: number, y: number}
  ) => {
    const {
      thickness, grooveDepth, bluntEdge, slopeWidth, plateWidth,
      groovePosition, grooveType, grooveAngle, bevel, bevelPosition, bevelLength, bevelHeight
    } = config

    // 右侧板材的8个点（顺时针：defghabc）：
    const points: {[key: string]: {x: number, y: number}} = {}

    // 计算对称轴位置（左侧D点位置 + 根部间隙的一半）
    const symmetryAxisX = leftDPoint.x + (config.rootGap || 0) / 2

    // d点：钝边起始点（对应左侧的D点）
    points.d = {x: symmetryAxisX, y: originY}

    // e点：钝边终止点（对应左侧的E点）
    if (bluntEdge === 0) {
      points.e = points.d
    } else {
      points.e = {x: symmetryAxisX + bluntEdge, y: originY}
    }

    // f点：上坡口终止点
    const upperGrooveHeight = grooveDepth
    if (groovePosition === 'outer') {
      // 外坡口：ef为斜线
      points.f = {x: points.e.x + slopeWidth, y: originY + upperGrooveHeight}
    } else {
      // 内坡口：ef为竖直线
      points.f = {x: points.e.x, y: originY + upperGrooveHeight}
    }

    // g点：上边界削边终止点
    if (bevel && bevelPosition === 'outer') {
      points.g = {x: symmetryAxisX + plateWidth + bevelLength, y: originY + thickness}
    } else {
      points.g = {x: symmetryAxisX + plateWidth, y: originY + thickness}
    }

    // h点：右上角
    points.h = {x: symmetryAxisX + plateWidth, y: originY + thickness}

    // a点：右上角（重复h点）
    points.a = points.h

    // b点：上边界削边起始点
    if (bevel && bevelPosition === 'outer') {
      points.b = {x: symmetryAxisX + plateWidth + bevelLength, y: originY + thickness}
    } else {
      points.b = points.a
    }

    // c点：上坡口起始点
    points.c = {x: symmetryAxisX + plateWidth, y: originY + thickness}

    // 绘制右侧板材
    ctx.fillStyle = 'rgba(255, 140, 0, 0.3)'
    ctx.strokeStyle = '#333'
    ctx.lineWidth = 2

    ctx.beginPath()
    ctx.moveTo(points.d.x, points.d.y)

    // de：钝边
    ctx.lineTo(points.e.x, points.e.y)

    // ef：上坡口
    if (grooveType === 'V' || grooveType === 'X') {
      ctx.lineTo(points.f.x, points.f.y)
    } else if (grooveType === 'U' || grooveType === 'J') {
      // U型坡口用圆弧
      const centerX = points.e.x + slopeWidth / 2
      const centerY = points.e.y + grooveDepth
      const radius = grooveDepth
      ctx.arcTo(centerX + radius, centerY, centerX + radius, points.f.y, radius)
    }

    // fg：上削边
    ctx.lineTo(points.g.x, points.g.y)

    // gh：上边界
    ctx.lineTo(points.h.x, points.h.y)

    // ha：右侧竖直边
    ctx.lineTo(points.a.x, points.a.y)

    // ab：上削边
    ctx.lineTo(points.b.x, points.b.y)

    // bc：上边界
    ctx.lineTo(points.c.x, points.c.y)

    // cd：下坡口
    if (grooveType === 'V' || grooveType === 'X') {
      ctx.lineTo(points.d.x, points.d.y)
    } else if (grooveType === 'U' || grooveType === 'J') {
      // U型坡口用圆弧
      const centerX = points.c.x - slopeWidth / 2
      const centerY = points.c.y - grooveDepth
      const radius = grooveDepth
      ctx.arcTo(centerX - radius, centerY, centerX - radius, points.d.y, radius)
    }

    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    return points
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, width, height)

    // 设置坐标系原点在画布底部中心
    const originX = width / 2 - 200
    const originY = height - 50

    // 绘制坐标系
    drawCoordinateSystem(ctx, originX, originY, width, height)

    // 缩放比例（mm -> px）- 使用1:1比例
    const scale = 1

    // 板材宽度（用于显示）
    const plateWidth = 50 * scale

    // 计算全焊透坡口深度
    const leftGrooveDepth = (params.leftThickness - params.bluntEdge) / 2
    const rightGrooveDepth = (params.rightThickness - params.bluntEdge) / 2

    // 计算左右坡口斜面宽度
    const leftSlopeWidth = leftGrooveDepth * Math.tan((params.leftGrooveAngle / 2) * Math.PI / 180) * scale
    const rightSlopeWidth = rightGrooveDepth * Math.tan((params.rightGrooveAngle / 2) * Math.PI / 180) * scale

    // 绘制左侧板材（A点在原点）
    const leftPts = drawLeftPlate(ctx, originX, originY, {
      thickness: params.leftThickness * scale,
      grooveDepth: leftGrooveDepth * scale,
      bluntEdge: params.bluntEdge * scale,
      rootGap: params.rootGap * scale,
      slopeWidth: leftSlopeWidth,
      plateWidth,
      groovePosition: params.groovePosition,
      grooveType: params.grooveType,
      grooveAngle: params.leftGrooveAngle,
      bevel: params.leftBevel,
      bevelPosition: params.leftBevelPosition,
      bevelLength: (params.leftBevelLength || 0) * scale,
      bevelHeight: (params.leftBevelHeight || 0) * scale
    })
    setLeftPoints(leftPts)

    // 绘制右侧板材
    const rightPts = drawRightPlateDirect(ctx, originX, originY, {
      thickness: params.rightThickness * scale,
      grooveDepth: rightGrooveDepth * scale,
      bluntEdge: params.bluntEdge * scale,
      rootGap: params.rootGap * scale,
      slopeWidth: rightSlopeWidth,
      plateWidth,
      groovePosition: params.groovePosition,
      grooveType: params.grooveType,
      grooveAngle: params.rightGrooveAngle,
      bevel: params.rightBevel,
      bevelPosition: params.rightBevelPosition,
      bevelLength: (params.rightBevelLength || 0) * scale,
      bevelHeight: (params.rightBevelHeight || 0) * scale
    }, leftPts.D)
    setRightPoints(rightPts)

  }, [params, width, height])

  return (
    <div className="weld-joint-diagram-v3">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{border: '1px solid #ccc', backgroundColor: '#f9f9f9'}}
      />
      <div style={{marginTop: '10px', fontSize: '12px', color: '#666'}}>
        <div>左侧板材坐标点：</div>
        {Object.entries(leftPoints).map(([key, point]) => (
          <span key={key} style={{marginRight: '10px'}}>
            {key}: ({point.x.toFixed(1)}, {point.y.toFixed(1)})
          </span>
        ))}
        <div style={{marginTop: '5px'}}>右侧板材坐标点：</div>
        {Object.entries(rightPoints).map(([key, point]) => (
          <span key={key} style={{marginRight: '10px'}}>
            {key}: ({point.x.toFixed(1)}, {point.y.toFixed(1)})
          </span>
        ))}
      </div>
    </div>
  )
}

export default WeldJointDiagramGeneratorV3