import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Typography,
  Statistic,
  Avatar,
  Popconfirm,
  Badge,
  Tooltip,
  Switch,
  AutoComplete,
} from 'antd'
import {
  HomeOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
  EyeOutlined,
  StopOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import enterpriseService from '@/services/enterprise'
import { useEnterpriseFactories } from '@/hooks/useEnterprise'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

// 接口定义
interface SimpleEmployee {
  id: string
  user_id: string
  employee_number: string
  name: string
  email: string
  phone: string
  role: 'admin' | 'manager' | 'employee'
  position: string
  department: string
  joined_at: string
}

interface Factory {
  id: string
  name: string
  code: string
  address: string
  city: string
  contact_person: string
  contact_phone: string
  employee_count: number
  employees: SimpleEmployee[]  // 添加员工列表
  is_headquarters: boolean
  is_active: boolean
  created_at: string
}

// 中国城市列表
const CHINA_CITIES = [
  // 直辖市
  '北京', '上海', '天津', '重庆',
  // 省会城市
  '石家庄', '太原', '呼和浩特', '沈阳', '长春', '哈尔滨', '南京', '杭州', '合肥', '福州',
  '南昌', '济南', '郑州', '武汉', '长沙', '广州', '南宁', '海口', '成都', '贵阳',
  '昆明', '拉萨', '西安', '兰州', '西宁', '银川', '乌鲁木齐',
  // 主要地级市
  '深圳', '珠海', '汕头', '佛山', '韶关', '湛江', '肇庆', '江门', '茂名', '惠州',
  '梅州', '汕尾', '河源', '阳江', '清远', '东莞', '中山', '潮州', '揭阳', '云浮',
  '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦',
  '铁岭', '朝阳', '葫芦岛', '长春', '吉林', '四平', '辽源', '通化', '白山', '松原',
  '白城', '延边', '哈尔滨', '齐齐哈尔', '鸡西', '鹤岗', '双鸭山', '大庆', '伊春',
  '佳木斯', '七台河', '牡丹江', '黑河', '绥化', '大兴安岭', '南京', '无锡', '徐州',
  '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁',
  '杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州',
  '丽水', '合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山',
  '滁州', '阜阳', '六安', '亳州', '池州', '宣城', '福州', '厦门', '莆田', '三明',
  '泉州', '漳州', '南平', '龙岩', '宁德', '南昌', '景德镇', '萍乡', '九江', '新余',
  '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶', '济南', '青岛', '淄博', '枣庄',
  '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '莱芜', '临沂', '德州',
  '聊城', '滨州', '菏泽', '郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡',
  '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店',
  '武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州', '荆门', '孝感', '荆州', '黄冈',
  '咸宁', '随州', '长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界',
  '益阳', '郴州', '永州', '怀化', '娄底', '广州', '韶关', '深圳', '珠海', '汕头',
  '佛山', '江门', '湛江', '茂名', '肇庆', '惠州', '梅州', '汕尾', '河源', '阳江',
  '清远', '东莞', '中山', '潮州', '揭阳', '云浮', '南宁', '柳州', '桂林', '梧州',
  '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左',
  '海口', '三亚', '三沙', '儋州', '成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳',
  '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州', '雅安',
  '巴中', '资阳', '贵阳', '六盘水', '遵义', '安顺', '毕节', '铜仁', '昆明', '曲靖',
  '玉溪', '保山', '昭通', '丽江', '普洱', '临沧', '拉萨', '日喀则', '昌都', '林芝',
  '山南', '那曲', '阿里', '西安', '铜川', '宝鸡', '咸阳', '渭南', '延安', '汉中',
  '榆林', '安康', '商洛', '兰州', '嘉峪关', '金昌', '白银', '天水', '武威', '张掖',
  '平凉', '酒泉', '庆阳', '定西', '陇南', '西宁', '海东', '银川', '石嘴山', '吴忠',
  '固原', '中卫', '乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '昌吉', '博尔塔拉', '巴音郭楞',
  '阿克苏', '克孜勒苏', '喀什', '和田', '伊犁', '塔城', '阿勒泰', '香港', '澳门'
]

const Factories: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit'>('create')
  const [selectedFactory, setSelectedFactory] = useState<Factory | null>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [cityFilter, setCityFilter] = useState<string>('')

  // 使用工厂管理Hook
  const {
    factories,
    loading,
    total,
    loadFactories,
    createFactory,
    updateFactory,
    deleteFactory,
    toggleFactoryStatus,
  } = useEnterpriseFactories({
    is_active: !filterStatus ? undefined : filterStatus === 'active',
  })

  // 统计数据
  const getStatistics = () => {
    const total = factories.length
    const active = factories.filter(f => f.is_active).length
    const inactive = factories.filter(f => !f.is_active).length
    const headquarters = factories.filter(f => f.is_headquarters).length

    return { total, active, inactive, headquarters }
  }

  const stats = getStatistics()

  // 过滤数据
  const filteredFactories = factories.filter(factory => {
    const matchSearch = !searchText ||
      factory.name.toLowerCase().includes(searchText.toLowerCase()) ||
      factory.code.toLowerCase().includes(searchText.toLowerCase()) ||
      factory.address.toLowerCase().includes(searchText.toLowerCase())
    const matchStatus = !filterStatus ||
      (filterStatus === 'active' && factory.is_active) ||
      (filterStatus === 'inactive' && !factory.is_active)
    const matchCity = !cityFilter || factory.city === cityFilter
    return matchSearch && matchStatus && matchCity
  })

  // 工厂列表列配置
  const columns: ColumnsType<Factory> = [
    {
      title: '工厂信息',
      key: 'factory',
      render: (_, record) => (
        <Space>
          <Avatar icon={<HomeOutlined />} />
          <div>
            <div>
              <Text strong>{record.name}</Text>
              {record.is_headquarters && <Tag color="red" className="ml-2">总部</Tag>}
            </div>
            <div>
              <Text type="secondary" className="text-xs">{record.code}</Text>
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '地址',
      key: 'address',
      render: (_, record) => (
        <div>
          <div>
            <EnvironmentOutlined className="mr-1" />
            <Text className="text-xs">{record.address}</Text>
          </div>
          <div>
            <Text type="secondary" className="text-xs">{record.city}</Text>
          </div>
        </div>
      ),
    },
    {
      title: '联系人',
      key: 'contact',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <Text strong>{record.contact_person}</Text>
          </div>
          <div>
            <PhoneOutlined className="mr-1" />
            <Text className="text-xs">{record.contact_phone}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '员工数量',
      dataIndex: 'employee_count',
      key: 'employee_count',
      render: (count) => (
        <Badge count={count} showZero style={{ backgroundColor: '#52c41a' }} />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => (
        <Badge
          status={active ? 'success' : 'error'}
          text={active ? '正常运营' : '已停用'}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedFactory(record)
              setDetailModalVisible(true)
            }}
          >
            查看
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedFactory(record)
              form.setFieldsValue(record)
              setModalType('edit')
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
          <Button
            type="text"
            icon={record.is_active ? <StopOutlined /> : <TeamOutlined />}
            onClick={() => {
              toggleFactoryStatus(record.id, !record.is_active)
            }}
          >
            {record.is_active ? '停用' : '启用'}
          </Button>
          <Popconfirm
            title="确定要删除这个工厂吗？"
            description="删除后无法恢复，请谨慎操作。"
            onConfirm={() => deleteFactory(record.id)}
            okText="确定"
            cancelText="取消"
            okType="danger"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 创建工厂
  const handleCreateFactory = () => {
    form.validateFields().then(values => {
      createFactory(values).then((success) => {
        if (success) {
          setModalVisible(false)
          form.resetFields()
          loadFactories()
        }
      })
    })
  }

  // 更新工厂
  const handleUpdateFactory = () => {
    if (selectedFactory) {
      form.validateFields().then(values => {
        updateFactory(selectedFactory.id, values).then((success) => {
          if (success) {
            setModalVisible(false)
            form.resetFields()
            setSelectedFactory(null)
            loadFactories()
          }
        })
      })
    }
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>工厂管理</Title>
        <Text type="secondary">管理企业工厂信息和运营状态</Text>
      </div>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="工厂数量"
              value={stats.total}
              prefix={<HomeOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="正常运营"
              value={stats.active}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已停用"
              value={stats.inactive}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总部数量"
              value={stats.headquarters}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="搜索工厂名称、编码或地址"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="状态筛选"
              value={filterStatus}
              onChange={setFilterStatus}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="active">正常运营</Option>
              <Option value="inactive">已停用</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="城市筛选"
              value={cityFilter}
              onChange={setCityFilter}
              allowClear
              style={{ width: '100%' }}
              showSearch
              filterOption={(input, option) =>
                (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {CHINA_CITIES.map(city => (
                <Option key={city} value={city}>{city}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setModalType('create')
                  setSelectedFactory(null)
                  form.resetFields()
                  setModalVisible(true)
                }}
              >
                创建工厂
              </Button>
              <Button icon={<ExportOutlined />}>
                导出数据
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 工厂列表 */}
      <Card title="工厂列表">
        <Table
          columns={columns}
          dataSource={filteredFactories}
          rowKey={(record) => `${record.id}_${record.code}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 创建/编辑工厂弹窗 */}
      <Modal
        title={modalType === 'create' ? '创建工厂' : '编辑工厂'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setSelectedFactory(null)
        }}
        onOk={modalType === 'create' ? handleCreateFactory : handleUpdateFactory}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_headquarters: false,
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="工厂名称"
                rules={[{ required: true, message: '请输入工厂名称' }]}
              >
                <Input placeholder="请输入工厂名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="工厂编码"
                rules={[{ required: true, message: '请输入工厂编码' }]}
              >
                <Input placeholder="请输入工厂编码" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="address"
            label="详细地址"
            rules={[{ required: true, message: '请输入详细地址' }]}
          >
            <TextArea placeholder="请输入详细地址" rows={2} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="city"
                label="城市"
                rules={[{ required: true, message: '请输入城市' }]}
              >
                <AutoComplete
                  placeholder="请输入或选择城市"
                  options={CHINA_CITIES.map(city => ({ value: city, label: city }))}
                  filterOption={(inputValue, option) =>
                    option?.value.toLowerCase().includes(inputValue.toLowerCase())
                  }
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="contact_person"
                label="联系人"
                rules={[{ required: true, message: '请输入联系人' }]}
              >
                <Input placeholder="请输入联系人" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="contact_phone"
            label="联系电话"
            rules={[{ required: true, message: '请输入联系电话' }]}
          >
            <Input placeholder="请输入联系电话" />
          </Form.Item>

          <Form.Item
            name="is_headquarters"
            label="设为总部"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 工厂详情弹窗 */}
      <Modal
        title="工厂详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedFactory && (
          <div>
            <Row gutter={16} className="mb-4">
              <Col span={6}>
                <div className="text-center">
                  <Avatar size={80} icon={<HomeOutlined />} />
                  <div className="mt-2">
                    <Title level={4}>{selectedFactory.name}</Title>
                    <Tag color="blue">{selectedFactory.code}</Tag>
                    {selectedFactory.is_headquarters && (
                      <Tag color="red" className="ml-2">总部</Tag>
                    )}
                  </div>
                </div>
              </Col>
              <Col span={18}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>状态：</Text>
                    <Badge
                      status={selectedFactory.is_active ? 'success' : 'error'}
                      text={selectedFactory.is_active ? '正常运营' : '已停用'}
                      className="ml-2"
                    />
                  </Col>
                  <Col span={12}>
                    <Text strong>城市：</Text> {selectedFactory.city}
                  </Col>
                  <Col span={12}>
                    <Text strong>创建时间：</Text> {dayjs(selectedFactory.created_at).format('YYYY-MM-DD')}
                  </Col>
                  <Col span={12}>
                    <Text strong>员工数量：</Text> {selectedFactory.employee_count} 人
                  </Col>
                </Row>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="基本信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>工厂编码：</Text>
                      <Tag color="blue" className="ml-2">{selectedFactory.code}</Tag>
                    </div>
                    <div>
                      <Text strong>详细地址：</Text>
                      <Text className="ml-2">{selectedFactory.address}</Text>
                    </div>
                    <div>
                      <Text strong>所在城市：</Text>
                      <Text className="ml-2">{selectedFactory.city}</Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="联系信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>联系人：</Text>
                      <Text className="ml-2">{selectedFactory.contact_person}</Text>
                    </div>
                    <div>
                      <Text strong>联系电话：</Text>
                      <Text className="ml-2">{selectedFactory.contact_phone}</Text>
                    </div>
                    <div>
                      <Text strong>员工总数：</Text>
                      <Badge count={selectedFactory.employee_count} className="ml-2" />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>

            <Card title="工厂设置" size="small" className="mt-4">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <div>
                    <Text strong>总部标识：</Text>
                    <Tag color={selectedFactory.is_headquarters ? 'red' : 'default'} className="ml-2">
                      {selectedFactory.is_headquarters ? '是总部' : '普通工厂'}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <div>
                    <Text strong>运营状态：</Text>
                    <Badge
                      status={selectedFactory.is_active ? 'success' : 'error'}
                      text={selectedFactory.is_active ? '正常运营' : '已停用'}
                      className="ml-2"
                    />
                  </div>
                </Col>
              </Row>
            </Card>

            {/* 员工列表 */}
            <Card title={<><TeamOutlined /> 工厂员工列表</>} size="small" className="mt-4">
              {selectedFactory.employees && selectedFactory.employees.length > 0 ? (
                <Table
                  dataSource={selectedFactory.employees}
                  rowKey={(record) => `${record.id}_${record.employee_number}`}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: '员工',
                      dataIndex: 'name',
                      key: 'name',
                      render: (text, record) => (
                        <Space>
                          <Avatar size="small" icon={<TeamOutlined />} />
                          <div>
                            <div>{text}</div>
                            <Text type="secondary" style={{ fontSize: 12 }}>{record.email}</Text>
                          </div>
                        </Space>
                      ),
                    },
                    {
                      title: '工号',
                      dataIndex: 'employee_number',
                      key: 'employee_number',
                    },
                    {
                      title: '部门',
                      dataIndex: 'department',
                      key: 'department',
                    },
                    {
                      title: '职位',
                      dataIndex: 'position',
                      key: 'position',
                    },
                    {
                      title: '角色',
                      dataIndex: 'role',
                      key: 'role',
                      render: (role) => (
                        <Tag color={role === 'admin' ? 'red' : role === 'manager' ? 'orange' : 'blue'}>
                          {role === 'admin' ? '管理员' : role === 'manager' ? '经理' : '员工'}
                        </Tag>
                      ),
                    },
                    {
                      title: '入职时间',
                      dataIndex: 'joined_at',
                      key: 'joined_at',
                      render: (text) => dayjs(text).format('YYYY-MM-DD'),
                    },
                  ]}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <Text type="secondary">该工厂暂无员工</Text>
                </div>
              )}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Factories