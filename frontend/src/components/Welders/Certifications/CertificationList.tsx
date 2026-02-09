/**
 * 焊工证书列表组件
 */
import React, { useState, useEffect } from 'react';
import { Button, Space, Empty, Spin, message, Select, Input, Row, Col } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import CertificationCard from './CertificationCard';
import CertificationModal from './CertificationModal';
import certificationService, {
  type WelderCertification,
  type CreateCertificationRequest,
} from '../../../services/certifications';
import { workspaceService } from '../../../services/workspace';

const { Option } = Select;

interface CertificationListProps {
  welderId: number;
}

/**
 * 证书列表组件
 */
const CertificationList: React.FC<CertificationListProps> = ({ welderId }) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
  const [certifications, setCertifications] = useState<WelderCertification[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingCertification, setEditingCertification] = useState<WelderCertification | undefined>();
  const [submitting, setSubmitting] = useState(false);

  // 筛选条件
  const [filterSystem, setFilterSystem] = useState<string | undefined>();
  const [filterStatus, setFilterStatus] = useState<string | undefined>();
  const [searchText, setSearchText] = useState('');

  // 加载证书列表
  const loadCertifications = async () => {
    if (!currentWorkspace) return;

    setLoading(true);
    try {
      const response = await certificationService.getList(
        welderId,
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      );
      setCertifications(response.items || []);
    } catch (error: any) {
      message.error(error.message || '加载证书列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCertifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [welderId]);

  // 打开添加模态框
  const handleAdd = () => {
    setEditingCertification(undefined);
    setModalVisible(true);
  };

  // 打开编辑模态框
  const handleEdit = (certification: WelderCertification) => {
    setEditingCertification(certification);
    setModalVisible(true);
  };

  // 删除证书
  const handleDelete = async (certificationId: number) => {
    if (!currentWorkspace) return;

    try {
      await certificationService.delete(
        welderId,
        certificationId,
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      );
      message.success('证书删除成功');
      loadCertifications();
    } catch (error: any) {
      message.error(error.message || '删除证书失败');
    }
  };

  // 提交表单
  const handleSubmit = async (values: CreateCertificationRequest) => {
    if (!currentWorkspace) return;

    setSubmitting(true);
    try {
      if (editingCertification) {
        // 更新证书
        await certificationService.update(
          welderId,
          editingCertification.id,
          values,
          currentWorkspace.type,
          currentWorkspace.company_id,
          currentWorkspace.factory_id
        );
        message.success('证书更新成功');
      } else {
        // 创建证书
        await certificationService.create(
          welderId,
          values,
          currentWorkspace.type,
          currentWorkspace.company_id,
          currentWorkspace.factory_id
        );
        message.success('证书添加成功');
      }
      setModalVisible(false);
      loadCertifications();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  // 筛选证书
  const filteredCertifications = certifications.filter((cert) => {
    // 按认证体系筛选
    if (filterSystem && cert.certification_system !== filterSystem) {
      return false;
    }

    // 按状态筛选
    if (filterStatus && cert.status !== filterStatus) {
      return false;
    }

    // 按搜索文本筛选
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      return (
        cert.certification_number.toLowerCase().includes(searchLower) ||
        cert.certification_type.toLowerCase().includes(searchLower) ||
        (cert.certification_system && cert.certification_system.toLowerCase().includes(searchLower)) ||
        (cert.issuing_authority && cert.issuing_authority.toLowerCase().includes(searchLower)) ||
        (cert.project_name && cert.project_name.toLowerCase().includes(searchLower))
      );
    }

    return true;
  });

  return (
    <div>
      {/* 工具栏 */}
      <div style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Space>
              <Input
                placeholder="搜索证书编号、类型、工艺、材料..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: 300 }}
                allowClear
              />
              <Select
                placeholder="认证体系"
                value={filterSystem}
                onChange={setFilterSystem}
                style={{ width: 150 }}
                allowClear
              >
                <Option value="ASME">ASME</Option>
                <Option value="国标">国标</Option>
                <Option value="欧标">欧标</Option>
                <Option value="AWS">AWS</Option>
                <Option value="API">API</Option>
                <Option value="DNV">DNV</Option>
              </Select>
              <Select
                placeholder="证书状态"
                value={filterStatus}
                onChange={setFilterStatus}
                style={{ width: 120 }}
                allowClear
              >
                <Option value="valid">有效</Option>
                <Option value="expiring_soon">即将过期</Option>
                <Option value="expired">已过期</Option>
                <Option value="suspended">已暂停</Option>
                <Option value="revoked">已吊销</Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加证书
            </Button>
          </Col>
        </Row>
      </div>

      {/* 证书列表 */}
      <Spin spinning={loading}>
        {filteredCertifications.length > 0 ? (
          <div>
            {filteredCertifications.map((cert) => (
              <CertificationCard
                key={cert.id}
                certification={cert}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : (
          <Empty
            description={
              certifications.length === 0
                ? '暂无证书记录'
                : '没有符合筛选条件的证书'
            }
          >
            {certifications.length === 0 && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                添加第一个证书
              </Button>
            )}
          </Empty>
        )}
      </Spin>

      {/* 添加/编辑模态框 */}
      <CertificationModal
        visible={modalVisible}
        certification={editingCertification}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        loading={submitting}
      />
    </div>
  );
};

export default CertificationList;

