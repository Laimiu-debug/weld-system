/**
 * 焊接接头示意图生成器 V2 测试页面
 */

import React, { useState } from 'react'
import { Card, Form, InputNumber, Select, Switch, Space, Row, Col, Divider } from 'antd'
import WeldJointDiagramGeneratorV2 from '../components/WPS/WeldJointDiagramGeneratorV2'

const { Option } = Select

const TestWeldJointV2: React.FC = () => {
  const [params, setParams] = useState({
    grooveType: 'V' as 'V' | 'U' | 'K' | 'J' | 'X' | 'I',
    groovePosition: 'outer' as 'outer' | 'inner',
    
    leftThickness: 10,
    leftGrooveAngle: 30,
    leftGrooveDepth: 8,
    leftBevel: false,
    leftBevelPosition: 'outer' as 'outer' | 'inner',
    leftBevelLength: 5,
    leftBevelHeight: 2,
    
    rightThickness: 10,
    rightGrooveAngle: 30,
    rightGrooveDepth: 8,
    rightBevel: false,
    rightBevelPosition: 'outer' as 'outer' | 'inner',
    rightBevelLength: 5,
    rightBevelHeight: 2,
    
    bluntEdge: 2,
    rootGap: 2
  })

  const handleChange = (field: string, value: any) => {
    setParams(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>焊接接头示意图生成器 V2 - 测试页面</h1>
      
      <Row gutter={24}>
        <Col span={16}>
          <WeldJointDiagramGeneratorV2 params={params} width={800} height={600} />
        </Col>
        
        <Col span={8}>
          <Card title="参数设置" size="small">
            <Form layout="vertical" size="small">
              <Divider orientation="left">坡口类型</Divider>
              
              <Form.Item label="坡口型式">
                <Select 
                  value={params.grooveType} 
                  onChange={(v) => handleChange('grooveType', v)}
                >
                  <Option value="V">V型</Option>
                  <Option value="U">U型</Option>
                  <Option value="K">K型</Option>
                  <Option value="J">J型</Option>
                  <Option value="X">X型</Option>
                  <Option value="I">I型</Option>
                </Select>
              </Form.Item>
              
              <Form.Item label="坡口位置">
                <Select 
                  value={params.groovePosition} 
                  onChange={(v) => handleChange('groovePosition', v)}
                >
                  <Option value="outer">外坡口（上侧）</Option>
                  <Option value="inner">内坡口（下侧）</Option>
                </Select>
              </Form.Item>

              <Divider orientation="left">左侧板材</Divider>
              
              <Form.Item label="板厚 (mm)">
                <InputNumber 
                  min={1} 
                  max={50} 
                  value={params.leftThickness}
                  onChange={(v) => handleChange('leftThickness', v || 10)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="坡口角 (°)">
                <InputNumber 
                  min={0} 
                  max={90} 
                  value={params.leftGrooveAngle}
                  onChange={(v) => handleChange('leftGrooveAngle', v || 30)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="坡口深度 (mm)">
                <InputNumber 
                  min={1} 
                  max={50} 
                  value={params.leftGrooveDepth}
                  onChange={(v) => handleChange('leftGrooveDepth', v || 8)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="启用削边">
                <Switch 
                  checked={params.leftBevel}
                  onChange={(v) => handleChange('leftBevel', v)}
                />
              </Form.Item>
              
              {params.leftBevel && (
                <>
                  <Form.Item label="削边位置">
                    <Select
                      value={params.leftBevelPosition}
                      onChange={(v) => handleChange('leftBevelPosition', v)}
                    >
                      <Option value="outer">上边界削边</Option>
                      <Option value="inner">下边界削边</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item label="削边长度 (mm)">
                    <InputNumber 
                      min={1} 
                      max={20} 
                      value={params.leftBevelLength}
                      onChange={(v) => handleChange('leftBevelLength', v || 5)}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                  
                  <Form.Item label="削边高度 (mm)">
                    <InputNumber 
                      min={0.5} 
                      max={10} 
                      value={params.leftBevelHeight}
                      onChange={(v) => handleChange('leftBevelHeight', v || 2)}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </>
              )}

              <Divider orientation="left">右侧板材</Divider>
              
              <Form.Item label="板厚 (mm)">
                <InputNumber 
                  min={1} 
                  max={50} 
                  value={params.rightThickness}
                  onChange={(v) => handleChange('rightThickness', v || 10)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="坡口角 (°)">
                <InputNumber 
                  min={0} 
                  max={90} 
                  value={params.rightGrooveAngle}
                  onChange={(v) => handleChange('rightGrooveAngle', v || 30)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="坡口深度 (mm)">
                <InputNumber 
                  min={1} 
                  max={50} 
                  value={params.rightGrooveDepth}
                  onChange={(v) => handleChange('rightGrooveDepth', v || 8)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="启用削边">
                <Switch 
                  checked={params.rightBevel}
                  onChange={(v) => handleChange('rightBevel', v)}
                />
              </Form.Item>
              
              {params.rightBevel && (
                <>
                  <Form.Item label="削边位置">
                    <Select
                      value={params.rightBevelPosition}
                      onChange={(v) => handleChange('rightBevelPosition', v)}
                    >
                      <Option value="outer">上边界削边</Option>
                      <Option value="inner">下边界削边</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item label="削边长度 (mm)">
                    <InputNumber 
                      min={1} 
                      max={20} 
                      value={params.rightBevelLength}
                      onChange={(v) => handleChange('rightBevelLength', v || 5)}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                  
                  <Form.Item label="削边高度 (mm)">
                    <InputNumber 
                      min={0.5} 
                      max={10} 
                      value={params.rightBevelHeight}
                      onChange={(v) => handleChange('rightBevelHeight', v || 2)}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </>
              )}

              <Divider orientation="left">根部参数</Divider>
              
              <Form.Item label="钝边 (mm)">
                <InputNumber 
                  min={0} 
                  max={10} 
                  value={params.bluntEdge}
                  onChange={(v) => handleChange('bluntEdge', v || 2)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              
              <Form.Item label="根部间隙 (mm)">
                <InputNumber 
                  min={0} 
                  max={10} 
                  value={params.rootGap}
                  onChange={(v) => handleChange('rootGap', v || 2)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>

      <Card title="测试说明" style={{ marginTop: 24 }}>
        <h3>绘制逻辑验证：</h3>
        <ol>
          <li><strong>左侧板材绘制顺序：</strong>
            <ul>
              <li>从左下角起始点开始</li>
              <li>绘制下边界（判断是否有削边）</li>
              <li>到达根部后，根据坡口类型绘制：
                <ul>
                  <li>内坡口：先绘制坡口，再绘制钝边</li>
                  <li>外坡口：先绘制钝边，再绘制坡口</li>
                </ul>
              </li>
              <li>绘制上边界（判断是否有削边）</li>
            </ul>
          </li>
          <li><strong>右侧板材起始点：</strong>
            <ul>
              <li>Y坐标：从左侧板钝边的终点获取</li>
              <li>X坐标：左侧板钝边终点的X坐标 + 根部间隙</li>
            </ul>
          </li>
          <li><strong>右侧板材绘制顺序：</strong>
            <ul>
              <li>内坡口：向上判断上边界削边并绘制，向下绘制钝边→坡口斜面→判断下边界削边</li>
              <li>外坡口：向上绘制坡口斜面→判断上边界削边，向下绘制钝边→判断下边界削边</li>
            </ul>
          </li>
          <li><strong>削边说明：</strong>
            <ul>
              <li>削边只与板材的上下边界有关，与内外坡口无关</li>
              <li>上边界削边：bevelPosition = 'outer'</li>
              <li>下边界削边：bevelPosition = 'inner'</li>
            </ul>
          </li>
        </ol>
        
        <h3>测试建议：</h3>
        <ul>
          <li>测试不同的坡口类型（V、U、K、J、X、I）</li>
          <li>测试内坡口和外坡口</li>
          <li>测试不同的板厚组合</li>
          <li>测试削边功能：
            <ul>
              <li>上边界削边（outer）：在板材上表面</li>
              <li>下边界削边（inner）：在板材下表面</li>
            </ul>
          </li>
          <li>观察钝边标注线（红色虚线）是否正确</li>
          <li>观察根部间隙标注线（蓝色虚线）是否正确</li>
        </ul>
      </Card>
    </div>
  )
}

export default TestWeldJointV2

