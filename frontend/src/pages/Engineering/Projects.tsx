import React, { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Row,
  Space,
  Spin,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import {
  DeleteOutlined,
  FileSearchOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { DataRow, engineeringService } from "@/services/engineering";
import "./engineering.css";

const { Title, Text, Paragraph } = Typography;

const errorMessage = (error: any, fallback: string) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (typeof detail?.message === "string") return detail.message;
  return fallback;
};

const EngineeringProjects: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<DataRow[]>([]);
  const [products, setProducts] = useState<DataRow[]>([]);
  const [revisions, setRevisions] = useState<Record<string, DataRow[]>>({});
  const [active, setActive] = useState<DataRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [projectOpen, setProjectOpen] = useState(false);
  const [productOpen, setProductOpen] = useState(false);
  const [projectForm] = Form.useForm();
  const [productForm] = Form.useForm();

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await engineeringService.projects();
      setProjects(rows);
      if (rows.length)
        setActive((current) =>
          current && rows.some((x) => x.id === current.id) ? current : rows[0],
        );
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);
  useEffect(() => {
    if (!active) {
      setProducts([]);
      return;
    }
    void engineeringService.products(active.id).then(async (rows) => {
      setProducts(rows);
      const pairs = await Promise.all(
        rows.map(
          async (x) =>
            [x.id, await engineeringService.revisions(x.id)] as const,
        ),
      );
      setRevisions(Object.fromEntries(pairs));
    });
  }, [active]);

  const createProject = async () => {
    const values = await projectForm.validateFields();
    await engineeringService.createProject(values);
    message.success("工程已创建");
    setProjectOpen(false);
    projectForm.resetFields();
    await loadProjects();
  };
  const createProduct = async () => {
    if (!active) return;
    const values = await productForm.validateFields();
    await engineeringService.createProduct(active.id, values);
    message.success("产品已创建");
    setProductOpen(false);
    productForm.resetFields();
    setProducts(await engineeringService.products(active.id));
  };
  const upload = async (product: DataRow, file: File) => {
    try {
      const rev = await engineeringService.uploadDrawing(
        product.id,
        file,
        "上传新图纸版本",
      );
      message.success(`图纸版本 V${rev.revision_number} 已建立`);
      setRevisions((v) => ({
        ...v,
        [product.id]: [rev, ...(v[product.id] || [])],
      }));
      navigate(`/engineering/revisions/${rev.id}/review`);
    } catch (error) {
      message.error(errorMessage(error, "图纸上传失败，请检查文件格式后重试"));
    }
    return false;
  };

  const deleteProject = (project: DataRow) => {
    Modal.confirm({
      title: `删除工程“${project.name}”？`,
      content: "工程内未批准的产品和图纸将一并删除；已被下游数据引用时系统会阻止删除。",
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        try {
          await engineeringService.deleteProject(project.id);
          message.success("工程已删除");
          if (active?.id === project.id) setActive(null);
          await loadProjects();
        } catch (error) {
          message.error(errorMessage(error, "工程删除失败"));
          throw error;
        }
      },
    });
  };

  const deleteRevision = (product: DataRow, revision: DataRow) => {
    Modal.confirm({
      title: `删除图纸版本 V${revision.revision_number}？`,
      content: "未批准的图纸原件及解析结果将被删除；已批准或被下游引用的版本不能删除。",
      okText: "删除",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        try {
          await engineeringService.deleteRevision(revision.id);
          setRevisions((current) => ({
            ...current,
            [product.id]: (current[product.id] || []).filter(
              (item) => item.id !== revision.id,
            ),
          }));
          message.success("图纸版本已删除");
        } catch (error) {
          message.error(errorMessage(error, "图纸删除失败"));
          throw error;
        }
      },
    });
  };

  return (
    <div className="engineering-page">
      <div className="engineering-hero">
        <div>
          <Title level={2}>工程项目与产品图纸</Title>
          <Paragraph>
            把承压设备图纸转换为可审核的零部件、装配关系和焊缝数据，批准后作为后续匹配与焊序计算的唯一版本输入。
          </Paragraph>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setProjectOpen(true)}
        >
          新建工程
        </Button>
      </div>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={7}>
            <Card title="工程项目" className="engineering-list-card">
              <List
                dataSource={projects}
                locale={{
                  emptyText: <Empty description="先新建一个工程项目" />,
                }}
                renderItem={(item) => (
                  <List.Item
                    className={
                      active?.id === item.id
                        ? "engineering-project active"
                        : "engineering-project"
                    }
                    onClick={() => setActive(item)}
                    actions={[
                      <Button
                        key="delete"
                        type="text"
                        danger
                        aria-label={`删除工程 ${item.name}`}
                        icon={<DeleteOutlined />}
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteProject(item);
                        }}
                      />,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<FolderOpenOutlined />}
                      title={item.name}
                      description={
                        <Space>
                          <Text type="secondary">{item.code}</Text>
                          <Tag>{item.products || 0} 个产品</Tag>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          <Col xs={24} lg={17}>
            <Card
              title={active ? `${active.name} · 产品` : "产品"}
              extra={
                <Button
                  disabled={!active}
                  icon={<PlusOutlined />}
                  onClick={() => setProductOpen(true)}
                >
                  新建产品
                </Button>
              }
            >
              {!active ? (
                <Empty description="请选择工程" />
              ) : (
                <List
                  grid={{ gutter: 16, column: 1 }}
                  dataSource={products}
                  locale={{
                    emptyText: <Empty description="工程中还没有产品" />,
                  }}
                  renderItem={(product) => (
                    <List.Item>
                      <Card size="small" className="engineering-product">
                        <div className="engineering-product-head">
                          <div>
                            <Title level={4}>{product.name}</Title>
                            <Space>
                              <Text type="secondary">{product.code}</Text>
                              {product.product_type && (
                                <Tag>{product.product_type}</Tag>
                              )}
                              <Tag
                                color={
                                  product.status === "active"
                                    ? "green"
                                    : "default"
                                }
                              >
                                {product.status === "active"
                                  ? "已生效"
                                  : "草稿"}
                              </Tag>
                            </Space>
                          </div>
                          <Upload
                            accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff"
                            showUploadList={false}
                            beforeUpload={(file) => upload(product, file)}
                          >
                            <Button
                              type="primary"
                              ghost
                              icon={<UploadOutlined />}
                            >
                              上传新图纸
                            </Button>
                          </Upload>
                        </div>
                        <div className="engineering-revisions">
                          {(revisions[product.id] || []).map((rev) => (
                            <div className="revision-row" key={rev.id}>
                              <button
                                className="revision-chip"
                                onClick={() =>
                                  navigate(
                                    `/engineering/revisions/${rev.id}/review`,
                                  )
                                }
                              >
                                <FileSearchOutlined />
                                <span>
                                  V{rev.revision_number} · {rev.drawing_filename}
                                </span>
                                <Tag
                                  color={
                                    rev.status === "approved"
                                      ? "green"
                                      : rev.parse_status === "failed"
                                        ? "red"
                                        : "orange"
                                  }
                                >
                                  {rev.status === "approved"
                                    ? "已批准"
                                    : rev.parse_status === "completed"
                                      ? "待审核"
                                      : rev.parse_status === "failed"
                                        ? "解析失败"
                                        : "待解析"}
                                </Tag>
                              </button>
                              <Button
                                danger
                                type="text"
                                aria-label={`删除图纸版本 V${rev.revision_number}`}
                                icon={<DeleteOutlined />}
                                onClick={() => deleteRevision(product, rev)}
                              />
                            </div>
                          ))}
                          {!(revisions[product.id] || []).length && (
                            <Text type="secondary">尚未上传图纸</Text>
                          )}
                        </div>
                      </Card>
                    </List.Item>
                  )}
                />
              )}
            </Card>
          </Col>
        </Row>
      </Spin>
      <Modal
        title="新建工程"
        open={projectOpen}
        onOk={() => void createProject()}
        onCancel={() => setProjectOpen(false)}
      >
        <Form form={projectForm} layout="vertical">
          <Form.Item name="code" label="工程编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="工程名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="说明">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="新建产品"
        open={productOpen}
        onOk={() => void createProduct()}
        onCancel={() => setProductOpen(false)}
      >
        <Form form={productForm} layout="vertical">
          <Form.Item name="code" label="产品编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="产品名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="product_type" label="产品类型">
            <Input placeholder="如：换热器、储罐、反应器" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
export default EngineeringProjects;
