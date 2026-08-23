import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import {
  ApartmentOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  DiffOutlined,
  FileProtectOutlined,
  HolderOutlined,
  LockOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  UnlockOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { engineeringService, RevisionDetail } from "@/services/engineering";
import {
  SequenceDetail,
  SequenceRow,
  sequenceService,
} from "@/services/sequence";
import "./sequence.css";

const { Title, Text, Paragraph } = Typography;
const statusMeta: Record<string, { label: string; color: string }> = {
  draft: { label: "草稿", color: "default" },
  pending: { label: "审批中", color: "processing" },
  approved: { label: "已批准冻结", color: "green" },
  rejected: { label: "已拒绝", color: "red" },
  returned: { label: "已退回", color: "orange" },
  superseded: { label: "已被新版本替代", color: "default" },
};
const typeMeta: Record<string, { label: string; color: string }> = {
  assembly: { label: "装配", color: "blue" },
  weld: { label: "焊接", color: "orange" },
  nde: { label: "NDE", color: "purple" },
  pwht: { label: "PWHT", color: "volcano" },
  inspection: { label: "检验", color: "green" },
  closure: { label: "封闭确认", color: "gold" },
};

interface SortableStepProps {
  item: SequenceRow;
  editable: boolean;
  locallyLocked: boolean;
  prerequisites: string[];
  onInspect: (item: SequenceRow) => void;
  onLock: (id: string) => void;
}

const SortableStep: React.FC<SortableStepProps> = ({
  item,
  editable,
  locallyLocked,
  prerequisites,
  onInspect,
  onLock,
}) => {
  const locked = item.is_locked || locallyLocked;
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id, disabled: !editable || locked });
  return (
    <article
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={`sequence-step ${isDragging ? "is-dragging" : ""}`}
      aria-label={`步骤 ${item.order_index} ${item.title}`}
    >
      <button
        className="sequence-step__handle"
        type="button"
        disabled={!editable || locked}
        aria-label={locked ? "步骤已锁定" : `拖动 ${item.title}`}
        {...attributes}
        {...listeners}
      >
        {locked ? <LockOutlined /> : <HolderOutlined />}
      </button>
      <div className="sequence-step__index">{item.order_index}</div>
      <div className="sequence-step__body">
        <Space wrap>
          <Tag color={typeMeta[item.step_type]?.color}>
            {typeMeta[item.step_type]?.label || item.step_type}
          </Tag>
          <Text strong>{item.title}</Text>
          <Text type="secondary">{item.phase}</Text>
        </Space>
        <Paragraph
          ellipsis={{ rows: 2 }}
          className="sequence-step__explanation"
        >
          {item.explanation}
        </Paragraph>
        <Space wrap size={[4, 4]}>
          {(item.constraint_tags || []).map((tag: string) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
          {prerequisites.length > 0 && (
            <Text type="secondary">前置：{prerequisites.join("、")}</Text>
          )}
        </Space>
      </div>
      <Space direction="vertical" size={4}>
        <Button size="small" type="link" onClick={() => onInspect(item)}>
          查看依据
        </Button>
        {editable && (
          <Tooltip
            title={item.is_locked ? "模板关键节点不可解锁" : "锁定当前步骤位置"}
          >
            <Button
              size="small"
              icon={locked ? <LockOutlined /> : <UnlockOutlined />}
              disabled={item.is_locked}
              onClick={() => onLock(item.id)}
            >
              {locked ? "已锁定" : "锁定"}
            </Button>
          </Tooltip>
        )}
      </Space>
    </article>
  );
};

const WeldSequencePlanning: React.FC = () => {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState<RevisionDetail | null>(null);
  const [versions, setVersions] = useState<SequenceRow[]>([]);
  const [activeId, setActiveId] = useState("");
  const [detail, setDetail] = useState<SequenceDetail | null>(null);
  const [steps, setSteps] = useState<SequenceRow[]>([]);
  const [lockedIds, setLockedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [inspect, setInspect] = useState<SequenceRow | null>(null);
  const [compareResult, setCompareResult] = useState<SequenceRow | null>(null);
  const [release, setRelease] = useState<SequenceRow | null>(null);
  const [generateForm] = Form.useForm();
  const [saveForm] = Form.useForm();
  const [submitForm] = Form.useForm();
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [revision, history, production] = await Promise.all([
        engineeringService.detail(id),
        sequenceService.list(id),
        sequenceService.productionRelease(id),
      ]);
      setProduct(revision);
      setVersions(history);
      setRelease(production);
      setActiveId((current) => current || history[0]?.id || "");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!activeId) {
      setDetail(null);
      setSteps([]);
      return;
    }
    void sequenceService.detail(activeId).then((value) => {
      setDetail(value);
      setSteps(value.steps);
      setLockedIds([]);
    });
  }, [activeId]);

  const editable = ["draft", "rejected", "returned"].includes(
    detail?.revision.status,
  );
  const validation = detail?.revision.validation_result || {};
  const stepById = useMemo(
    () => Object.fromEntries(steps.map((item) => [item.id, item])),
    [steps],
  );
  const prerequisites = useMemo(() => {
    const result: Record<string, string[]> = {};
    for (const item of detail?.dependencies || []) {
      const before = stepById[item.predecessor_step_id];
      if (!before) continue;
      (result[item.successor_step_id] ||= []).push(before.title);
    }
    return result;
  }, [detail?.dependencies, stepById]);

  const generate = async () => {
    const values = await generateForm.validateFields();
    setWorking(true);
    try {
      const created = await sequenceService.generate(id, {
        strategies: {
          symmetric: values.symmetric ?? true,
          segmented: values.segmented ?? false,
          skip_weld: values.skip_weld ?? false,
          closed_space_first: true,
        },
      });
      message.success("已生成可验证的候选焊序");
      setGenerateOpen(false);
      await load();
      setActiveId(created.id);
    } finally {
      setWorking(false);
    }
  };

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    setSteps((current) => {
      const oldIndex = current.findIndex((item) => item.id === active.id);
      const newIndex = current.findIndex((item) => item.id === over.id);
      const proposed: SequenceRow[] = arrayMove(
        current,
        oldIndex,
        newIndex,
      ).map((item, index) => ({
        ...item,
        order_index: index + 1,
      }));
      const movedTemplateLock = current.some(
        (item, index) => item.is_locked && proposed[index]?.id !== item.id,
      );
      if (movedTemplateLock) {
        message.warning("不能跨越模板锁定节点，请在当前可调整区间内排序");
        return current;
      }
      return proposed;
    });
  };

  const saveOrder = async () => {
    if (!detail) return;
    const values = await saveForm.validateFields();
    setWorking(true);
    try {
      const created = await sequenceService.reorder(detail.revision.id, {
        ordered_step_ids: steps.map((item) => item.id),
        locked_step_ids: lockedIds,
        change_summary: values.change_summary,
      });
      message.success("调整已保存为新焊序版本，原版本保持不变");
      await load();
      setActiveId(created.id);
    } finally {
      setWorking(false);
    }
  };

  const recalculate = async () => {
    if (!detail) return;
    setWorking(true);
    try {
      const created = await sequenceService.recalculate(detail.revision.id);
      message.success("已按当前焊缝和 P4 快照生成新版本");
      await load();
      setActiveId(created.id);
    } finally {
      setWorking(false);
    }
  };

  const compare = async (rightId: string) => {
    if (!activeId || !rightId) return;
    setCompareResult(await sequenceService.compare(activeId, rightId));
  };

  const submit = async () => {
    if (!detail) return;
    const values = await submitForm.validateFields();
    setWorking(true);
    try {
      const updated = await sequenceService.submit(detail.revision.id, values);
      message.success(
        updated.status === "approved"
          ? "焊序已批准冻结"
          : "已进入现有审批工作流",
      );
      await load();
      setDetail(await sequenceService.detail(detail.revision.id));
    } finally {
      setWorking(false);
    }
  };

  return (
    <Spin spinning={loading || working}>
      <main className="sequence-page">
        <header className="sequence-header">
          <Space align="start">
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(`/engineering/revisions/${id}/matching`)}
              aria-label="返回 WPS 匹配"
            />
            <div>
              <Title level={2}>焊序编排</Title>
              <Paragraph>
                候选顺序可以调整；装配、可达性、NDE、PWHT与封闭空间约束始终由确定性规则校验。
              </Paragraph>
            </div>
          </Space>
          <Space wrap>
            <Button
              icon={<ReloadOutlined />}
              disabled={!detail}
              onClick={() => void recalculate()}
            >
              重新计算
            </Button>
            <Button
              type="primary"
              icon={<ApartmentOutlined />}
              onClick={() => setGenerateOpen(true)}
            >
              生成候选焊序
            </Button>
          </Space>
        </header>

        <Row gutter={[16, 16]}>
          <Col xs={12} lg={6}>
            <Card>
              <Statistic
                title="产品版本"
                value={`V${product?.revision.revision_number || "-"}`}
              />
            </Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card>
              <Statistic title="焊序步骤" value={steps.length} />
            </Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card>
              <Statistic
                title="强制依赖"
                value={
                  detail?.dependencies.filter((item) => item.is_mandatory)
                    .length || 0
                }
              />
            </Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card>
              <Statistic
                title="约束校验"
                value={validation.valid ? "通过" : detail ? "阻断" : "-"}
                prefix={
                  validation.valid ? (
                    <CheckCircleOutlined />
                  ) : (
                    <WarningOutlined />
                  )
                }
                valueStyle={{ color: validation.valid ? "#15803d" : "#c2410c" }}
              />
            </Card>
          </Col>
        </Row>

        <Alert
          className="sequence-release"
          type={release?.eligible ? "success" : "warning"}
          showIcon
          message={
            release?.eligible
              ? "当前已有可下发生产的批准焊序"
              : "当前焊序不可下发生产"
          }
          description={release?.reason}
        />

        <Card className="sequence-toolbar">
          <Space wrap>
            <Text strong>焊序版本</Text>
            <Select
              value={activeId || undefined}
              placeholder="请选择版本"
              style={{ minWidth: 220 }}
              options={versions.map((item) => ({
                value: item.id,
                label: `V${item.version_number} · ${statusMeta[item.status]?.label || item.status}`,
              }))}
              onChange={setActiveId}
            />
            {detail && (
              <Tag color={statusMeta[detail.revision.status]?.color}>
                {statusMeta[detail.revision.status]?.label ||
                  detail.revision.status}
              </Tag>
            )}
            <Select
              allowClear
              placeholder="与另一版本比较"
              style={{ minWidth: 210 }}
              suffixIcon={<DiffOutlined />}
              options={versions
                .filter((item) => item.id !== activeId)
                .map((item) => ({
                  value: item.id,
                  label: `与 V${item.version_number} 比较`,
                }))}
              onChange={(value) => void compare(value)}
            />
          </Space>
        </Card>

        {validation.issues?.length > 0 && (
          <Alert
            type="error"
            showIcon
            role="alert"
            message="当前方案存在阻断问题"
            description={
              <List
                size="small"
                dataSource={validation.issues}
                renderItem={(item: SequenceRow) => (
                  <List.Item>{item.message}</List.Item>
                )}
              />
            }
          />
        )}

        {steps.length ? (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={onDragEnd}
          >
            <SortableContext
              items={steps.map((item) => item.id)}
              strategy={verticalListSortingStrategy}
            >
              <section className="sequence-list" aria-label="焊序步骤列表">
                {steps.map((item) => (
                  <SortableStep
                    key={item.id}
                    item={item}
                    editable={editable}
                    locallyLocked={lockedIds.includes(item.id)}
                    prerequisites={prerequisites[item.id] || []}
                    onInspect={setInspect}
                    onLock={(stepId) =>
                      setLockedIds((current) =>
                        current.includes(stepId)
                          ? current.filter((value) => value !== stepId)
                          : [...current, stepId],
                      )
                    }
                  />
                ))}
              </section>
            </SortableContext>
          </DndContext>
        ) : (
          <Card>
            <Empty description="尚未生成焊序" />
          </Card>
        )}

        {detail && (
          <Card className="sequence-actions">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} lg={12}>
                <Form form={saveForm} layout="vertical">
                  <Form.Item
                    label="版本变更说明"
                    name="change_summary"
                    rules={[{ required: true, message: "请说明调整原因" }]}
                  >
                    <Input placeholder="例如：调整接管焊缝至封闭前完成" />
                  </Form.Item>
                  <Button
                    icon={<FileProtectOutlined />}
                    disabled={!editable}
                    onClick={() => void saveOrder()}
                  >
                    保存为新版本
                  </Button>
                </Form>
              </Col>
              <Col xs={24} lg={12}>
                <Form form={submitForm} layout="vertical">
                  <Form.Item label="审批说明" name="notes">
                    <Input placeholder="提交焊接工程师审批" />
                  </Form.Item>
                  <Button
                    type="primary"
                    icon={<SafetyCertificateOutlined />}
                    disabled={!editable || !validation.valid}
                    onClick={() => void submit()}
                  >
                    提交审批并冻结
                  </Button>
                </Form>
              </Col>
            </Row>
          </Card>
        )}

        <Modal
          title="生成压力容器候选焊序"
          open={generateOpen}
          onCancel={() => setGenerateOpen(false)}
          onOk={() => void generate()}
          okText="生成并校验"
        >
          <Alert
            type="info"
            showIcon
            message="策略不会绕过强制约束"
            description="对称、分段和跳焊只影响同等可执行步骤的施工策略；非法候选会被确定性规则排除。"
          />
          <Form
            form={generateForm}
            layout="vertical"
            initialValues={{
              symmetric: true,
              segmented: false,
              skip_weld: false,
            }}
          >
            <Form.Item name="symmetric" valuePropName="checked">
              <Checkbox>优先对称焊，降低变形风险</Checkbox>
            </Form.Item>
            <Form.Item name="segmented" valuePropName="checked">
              <Checkbox>启用分段焊策略</Checkbox>
            </Form.Item>
            <Form.Item name="skip_weld" valuePropName="checked">
              <Checkbox>启用跳焊策略</Checkbox>
            </Form.Item>
          </Form>
        </Modal>

        <Drawer
          title={inspect?.title || "步骤依据"}
          width={560}
          open={Boolean(inspect)}
          onClose={() => setInspect(null)}
        >
          {inspect && (
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="步骤编码">
                {inspect.step_code}
              </Descriptions.Item>
              <Descriptions.Item label="阶段">
                {inspect.phase}
              </Descriptions.Item>
              <Descriptions.Item label="确定性解释">
                {inspect.explanation}
              </Descriptions.Item>
              <Descriptions.Item label="约束标签">
                {(inspect.constraint_tags || []).join("、") || "无"}
              </Descriptions.Item>
              <Descriptions.Item label="WPS">
                {inspect.process_parameters?.wps?.wps_number || "不适用"}
              </Descriptions.Item>
              <Descriptions.Item label="PQR">
                {inspect.process_parameters?.pqr?.pqr_number || "不适用"}
              </Descriptions.Item>
              <Descriptions.Item label="检验节点">
                <pre>
                  {JSON.stringify(inspect.inspection_node || {}, null, 2)}
                </pre>
              </Descriptions.Item>
            </Descriptions>
          )}
        </Drawer>

        <Modal
          title="焊序版本差异"
          width={720}
          open={Boolean(compareResult)}
          onCancel={() => setCompareResult(null)}
          footer={<Button onClick={() => setCompareResult(null)}>关闭</Button>}
        >
          <Table
            rowKey="step_code"
            pagination={false}
            dataSource={compareResult?.moved || []}
            locale={{ emptyText: "步骤顺序没有变化" }}
            columns={[
              { title: "步骤", dataIndex: "step_code" },
              { title: "原位置", dataIndex: "from" },
              { title: "新位置", dataIndex: "to" },
            ]}
          />
          <Paragraph>
            新增：{compareResult?.added?.join("、") || "无"}
          </Paragraph>
          <Paragraph>
            移除：{compareResult?.removed?.join("、") || "无"}
          </Paragraph>
        </Modal>
      </main>
    </Spin>
  );
};

export default WeldSequencePlanning;
