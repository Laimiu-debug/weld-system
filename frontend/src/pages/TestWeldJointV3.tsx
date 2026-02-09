import React, { useState } from 'react'
import { Card, Form, InputNumber, Select, Switch, Space, Typography, Divider } from 'antd'
import WeldJointDiagramGeneratorV3 from '../components/WPS/WeldJointDiagramGeneratorV3'
import type { WeldJointParamsV3 } from '../components/WPS/WeldJointDiagramGeneratorV3'

const { Title, Text } = Typography
const { Option } = Select

const TestWeldJointV3: React.FC = () => {
  const [params, setParams] = useState<WeldJointParamsV3>({
    grooveType: 'V',
    groovePosition: 'outer',
    
    leftThickness: 8,
    leftGrooveAngle: 60,
    leftGrooveDepth: 6,
    leftBevel: false,
    leftBevelPosition: 'outer',
    leftBevelLength: 10,
    leftBevelHeight: 2,
    
    rightThickness: 8,
    rightGrooveAngle: 60,
    rightGrooveDepth: 6,
    rightBevel: false,
    rightBevelPosition: 'outer',
    rightBevelLength: 10,
    rightBevelHeight: 2,
    
    bluntEdge: 2,
    rootGap: 2
  })

  const updateParam = (key: keyof WeldJointParamsV3, value: any) => {
    setParams(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>焊接接头示意图生成器 V3 测试页面</Title>
      <Text type="secondary">基于8点逆时针绘制模式</Text>
      
      <Divider />

      <div style={{ display: 'flex', gap: '24px' }}>
        {/* 左侧参数面板 */}
        <Card title="参数设置" style={{ width: '400px' }}>
          <Form layout="vertical">
            <Form.Item label="坡口类型">
              <Select
                value={params.grooveType}
                onChange={(value) => updateParam('grooveType', value)}
              >
                <Option value="V">V型</Option>
                <Option value="U">U型</Option>
                <Option value="J">J型</Option>
                <Option value="X">X型</Option>
              </Select>
            </Form.Item>

            <Form.Item label="坡口位置">
              <Select
                value={params.groovePosition}
                onChange={(value) => updateParam('groovePosition', value)}
              >
                <Option value="outer">外坡口（从上侧开口）</Option>
                <Option value="inner">内坡口（从下侧开口）</Option>
              </Select>
            </Form.Item>

            <Divider>左侧板材</Divider>

            <Form.Item label="板厚 (mm)">
              <InputNumber
                value={params.leftThickness}
                onChange={(value) => updateParam('leftThickness', value || 0)}
                min={1}
                max={50}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="坡口角度 (°)">
              <InputNumber
                value={params.leftGrooveAngle}
                onChange={(value) => updateParam('leftGrooveAngle', value || 0)}
                min={0}
                max={90}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="坡口深度 (mm)">
              <InputNumber
                value={params.leftGrooveDepth}
                onChange={(value) => updateParam('leftGrooveDepth', value || 0)}
                min={0}
                max={50}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="是否有削边">
              <Switch
                checked={params.leftBevel}
                onChange={(checked) => updateParam('leftBevel', checked)}
              />
            </Form.Item>

            {params.leftBevel && (
              <>
                <Form.Item label="削边位置">
                  <Select
                    value={params.leftBevelPosition}
                    onChange={(value) => updateParam('leftBevelPosition', value)}
                  >
                    <Option value="outer">上边界削边</Option>
                    <Option value="inner">下边界削边</Option>
                  </Select>
                </Form.Item>

                <Form.Item label="削边长度 (mm)">
                  <InputNumber
                    value={params.leftBevelLength}
                    onChange={(value) => updateParam('leftBevelLength', value || 0)}
                    min={0}
                    max={50}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item label="削边高度 (mm)">
                  <InputNumber
                    value={params.leftBevelHeight}
                    onChange={(value) => updateParam('leftBevelHeight', value || 0)}
                    min={0}
                    max={10}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </>
            )}

            <Divider>右侧板材</Divider>

            <Form.Item label="板厚 (mm)">
              <InputNumber
                value={params.rightThickness}
                onChange={(value) => updateParam('rightThickness', value || 0)}
                min={1}
                max={50}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="坡口角度 (°)">
              <InputNumber
                value={params.rightGrooveAngle}
                onChange={(value) => updateParam('rightGrooveAngle', value || 0)}
                min={0}
                max={90}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="坡口深度 (mm)">
              <InputNumber
                value={params.rightGrooveDepth}
                onChange={(value) => updateParam('rightGrooveDepth', value || 0)}
                min={0}
                max={50}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="是否有削边">
              <Switch
                checked={params.rightBevel}
                onChange={(checked) => updateParam('rightBevel', checked)}
              />
            </Form.Item>

            {params.rightBevel && (
              <>
                <Form.Item label="削边位置">
                  <Select
                    value={params.rightBevelPosition}
                    onChange={(value) => updateParam('rightBevelPosition', value)}
                  >
                    <Option value="outer">上边界削边</Option>
                    <Option value="inner">下边界削边</Option>
                  </Select>
                </Form.Item>

                <Form.Item label="削边长度 (mm)">
                  <InputNumber
                    value={params.rightBevelLength}
                    onChange={(value) => updateParam('rightBevelLength', value || 0)}
                    min={0}
                    max={50}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item label="削边高度 (mm)">
                  <InputNumber
                    value={params.rightBevelHeight}
                    onChange={(value) => updateParam('rightBevelHeight', value || 0)}
                    min={0}
                    max={10}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </>
            )}

            <Divider>根部参数</Divider>

            <Form.Item label="钝边 (mm)">
              <InputNumber
                value={params.bluntEdge}
                onChange={(value) => updateParam('bluntEdge', value || 0)}
                min={0}
                max={10}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item label="根部间隙 (mm)">
              <InputNumber
                value={params.rootGap}
                onChange={(value) => updateParam('rootGap', value || 0)}
                min={0}
                max={10}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Form>
        </Card>

        {/* 右侧示意图 */}
        <Card title="焊接接头示意图" style={{ flex: 1 }}>
          <WeldJointDiagramGeneratorV3 params={params} width={800} height={400} />
          
          <Divider />
          
          <div>
            <Title level={5}>8点绘制模式说明</Title>
            <Text>
              <ul>
                <li><strong>A点</strong>：左下角原点</li>
                <li><strong>B点</strong>：下边界削边起始点</li>
                <li><strong>C点</strong>：下边界削边终止点 = 下坡口起始点</li>
                <li><strong>D点</strong>：下坡口终止点 = 钝边起始点</li>
                <li><strong>E点</strong>：钝边终止点 = 上坡口起始点</li>
                <li><strong>F点</strong>：上坡口终止点 = 上边界削边起始点</li>
                <li><strong>G点</strong>：上边界削边终止点</li>
                <li><strong>H点</strong>：左上角</li>
              </ul>
            </Text>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default TestWeldJointV3

