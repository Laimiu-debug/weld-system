/**
 * 焊接接头示意图生成器 V4 测试页面
 */
import React from 'react'
import { Card, Tabs, Space, Typography } from 'antd'
import WeldJointDiagramGeneratorV4 from '../components/WPS/WeldJointDiagramGeneratorV4'

const { Title, Paragraph, Text } = Typography
const { TabPane } = Tabs

const TestWeldJointV4: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={2}>焊接接头示意图生成器 V4</Title>
        <Paragraph>
          这是改进的 V4 版本，综合了前三个版本的优点，实现了以下核心功能：
        </Paragraph>
        
        <Space direction="vertical" size="small" style={{ marginBottom: 24 }}>
          <Text>✅ <strong>内外坡口支持</strong>：可以选择外坡口（从外侧开坡口）或内坡口（从内侧开坡口）</Text>
          <Text>✅ <strong>左右不同厚度</strong>：左右板材可以设置不同的厚度、坡口角度和坡口深度</Text>
          <Text>✅ <strong>削边实现</strong>：支持左右板材独立配置削边参数（位置、长度、高度）</Text>
          <Text>✅ <strong>三种对齐方式</strong>：</Text>
          <Space direction="vertical" size="small" style={{ marginLeft: 32 }}>
            <Text>• 中心线对齐：左右板材中心线对齐</Text>
            <Text>• 外侧对齐：外表面齐平（外坡口时为上表面，内坡口时为下表面）</Text>
            <Text>• 内侧对齐：内表面齐平（外坡口时为下表面，内坡口时为上表面）</Text>
          </Space>
          <Text>✅ <strong>清晰的绘制逻辑</strong>：采用8点逆时针绘制模式，代码结构清晰易维护</Text>
          <Text>✅ <strong>完整的参数化设计</strong>：所有关键尺寸均可配置</Text>
        </Space>

        <Tabs defaultActiveKey="1">
          <TabPane tab="V4 版本" key="1">
            <WeldJointDiagramGeneratorV4 />
          </TabPane>
          
          <TabPane tab="使用说明" key="2">
            <Card>
              <Title level={4}>参数说明</Title>
              
              <Title level={5}>基本参数</Title>
              <Paragraph>
                <ul>
                  <li><strong>坡口类型</strong>：V型、X型、U型、I型（方槽）</li>
                  <li><strong>坡口位置</strong>：
                    <ul>
                      <li>外坡口：从板材外侧（远离焊接区域的一侧）开坡口</li>
                      <li>内坡口：从板材内侧（靠近焊接区域的一侧）开坡口</li>
                    </ul>
                  </li>
                  <li><strong>对齐方式</strong>：
                    <ul>
                      <li>中心线对齐：左右板材的中心线对齐，适用于等厚度或对称焊接</li>
                      <li>外侧对齐：外表面齐平，适用于外观要求高的场合</li>
                      <li>内侧对齐：内表面齐平，适用于内部结构要求的场合</li>
                    </ul>
                  </li>
                </ul>
              </Paragraph>

              <Title level={5}>板材参数</Title>
              <Paragraph>
                <ul>
                  <li><strong>板厚</strong>：板材的厚度，单位mm</li>
                  <li><strong>坡口角度</strong>：坡口的倾斜角度，单位度（°）</li>
                  <li><strong>坡口深度</strong>：坡口的深度，应小于板厚，单位mm</li>
                </ul>
              </Paragraph>

              <Title level={5}>削边参数</Title>
              <Paragraph>
                削边（钝边）是指在板材边缘进行的厚度过渡处理：
                <ul>
                  <li><strong>削边位置</strong>：
                    <ul>
                      <li>外削边：在远离坡口的一侧削边</li>
                      <li>内削边：在靠近坡口的一侧削边</li>
                    </ul>
                  </li>
                  <li><strong>削边长度</strong>：削边过渡的水平长度，单位mm</li>
                  <li><strong>削边高度</strong>：削边造成的厚度变化量，单位mm</li>
                </ul>
              </Paragraph>

              <Title level={5}>根部参数</Title>
              <Paragraph>
                <ul>
                  <li><strong>钝边</strong>：坡口底部保留的平面宽度，用于防止烧穿，单位mm</li>
                  <li><strong>根部间隙</strong>：左右板材之间的间隙，单位mm</li>
                </ul>
              </Paragraph>
            </Card>
          </TabPane>

          <TabPane tab="典型应用场景" key="3">
            <Card>
              <Title level={4}>典型应用场景</Title>
              
              <Title level={5}>场景1：等厚度板材对接（中心线对齐）</Title>
              <Paragraph>
                <ul>
                  <li>左右板厚：12mm</li>
                  <li>坡口类型：V型</li>
                  <li>坡口位置：外坡口</li>
                  <li>对齐方式：中心线对齐</li>
                  <li>坡口角度：30°（左右各30°，总角度60°）</li>
                  <li>钝边：2mm</li>
                  <li>根部间隙：2mm</li>
                </ul>
              </Paragraph>

              <Title level={5}>场景2：不等厚度板材对接（外侧对齐）</Title>
              <Paragraph>
                <ul>
                  <li>左侧板厚：12mm，右侧板厚：10mm</li>
                  <li>坡口类型：V型</li>
                  <li>坡口位置：外坡口</li>
                  <li>对齐方式：外侧对齐（上表面齐平）</li>
                  <li>左侧坡口角度：30°，右侧坡口角度：35°</li>
                  <li>钝边：2mm</li>
                  <li>根部间隙：2mm</li>
                </ul>
              </Paragraph>

              <Title level={5}>场景3：带削边的板材对接</Title>
              <Paragraph>
                <ul>
                  <li>左右板厚：12mm</li>
                  <li>坡口类型：V型</li>
                  <li>坡口位置：外坡口</li>
                  <li>对齐方式：中心线对齐</li>
                  <li>左侧启用外削边：长度15mm，高度2mm</li>
                  <li>右侧启用内削边：长度15mm，高度2mm</li>
                </ul>
              </Paragraph>

              <Title level={5}>场景4：内坡口焊接（管道内部焊接）</Title>
              <Paragraph>
                <ul>
                  <li>左右板厚：10mm</li>
                  <li>坡口类型：V型</li>
                  <li>坡口位置：内坡口（从内侧开坡口）</li>
                  <li>对齐方式：外侧对齐（外表面齐平）</li>
                  <li>坡口角度：30°</li>
                  <li>钝边：2mm</li>
                  <li>根部间隙：2mm</li>
                </ul>
              </Paragraph>
            </Card>
          </TabPane>

          <TabPane tab="版本对比" key="4">
            <Card>
              <Title level={4}>版本演进历史</Title>
              
              <Title level={5}>V1 版本</Title>
              <Paragraph>
                <Text type="success">优点：</Text>
                <ul>
                  <li>完整的参数系统</li>
                  <li>支持多种接头类型</li>
                  <li>实现了三种对齐方式</li>
                </ul>
                <Text type="danger">问题：</Text>
                <ul>
                  <li>代码中有未定义变量引用</li>
                  <li>削边实现复杂，逻辑不够清晰</li>
                  <li>坐标计算较为复杂，难以维护</li>
                </ul>
              </Paragraph>

              <Title level={5}>V2 版本</Title>
              <Paragraph>
                <Text type="success">优点：</Text>
                <ul>
                  <li>简化了绘制逻辑</li>
                  <li>左右板材独立绘制</li>
                  <li>代码结构更清晰</li>
                </ul>
                <Text type="danger">问题：</Text>
                <ul>
                  <li>没有对齐方式支持</li>
                  <li>缺少UI表单</li>
                  <li>右侧板材起始点计算可能不准确</li>
                </ul>
              </Paragraph>

              <Title level={5}>V3 版本</Title>
              <Paragraph>
                <Text type="success">优点：</Text>
                <ul>
                  <li>采用8点逆时针绘制模式，概念清晰</li>
                  <li>支持U型和J型坡口的圆弧绘制</li>
                  <li>显示坐标点信息，便于调试</li>
                </ul>
                <Text type="danger">问题：</Text>
                <ul>
                  <li>移除了坡口深度参数，只支持全焊透</li>
                  <li>没有对齐方式支持</li>
                  <li>削边实现不完整</li>
                  <li>缺少UI表单</li>
                </ul>
              </Paragraph>

              <Title level={5}>V4 版本（当前版本）</Title>
              <Paragraph>
                <Text type="success" strong>综合改进：</Text>
                <ul>
                  <li>✅ 采用V3的8点绘制模式，逻辑清晰</li>
                  <li>✅ 恢复V1的完整参数系统和对齐方式</li>
                  <li>✅ 改进削边实现，支持内外削边</li>
                  <li>✅ 完整的UI表单</li>
                  <li>✅ 支持左右不同厚度板材</li>
                  <li>✅ 代码结构清晰，易于维护和扩展</li>
                </ul>
              </Paragraph>
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default TestWeldJointV4

