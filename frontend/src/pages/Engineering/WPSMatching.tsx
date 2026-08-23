import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  Progress,
  Radio,
  Row,
  Segmented,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  FileProtectOutlined,
  LinkOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { engineeringService, RevisionDetail } from "@/services/engineering";
import { MatchDetail, MatchRow, matchingService } from "@/services/matching";
import "./matching.css";

const { Title, Text, Paragraph } = Typography;
const statusMeta: Record<
  string,
  { label: string; color: string; icon: React.ReactNode }
> = {
  pass: { label: "通过", color: "green", icon: <CheckCircleOutlined /> },
  fail: { label: "不通过", color: "red", icon: <CloseCircleOutlined /> },
  boundary: {
    label: "规则边界",
    color: "orange",
    icon: <ExclamationCircleOutlined />,
  },
  insufficient: {
    label: "信息不足",
    color: "gold",
    icon: <ExclamationCircleOutlined />,
  },
};
const decisionMeta: Record<string, { label: string; color: string }> = {
  eligible: { label: "完整覆盖", color: "green" },
  needs_confirmation: { label: "需要复核", color: "orange" },
  not_eligible: { label: "不符合", color: "red" },
};
const dimensionLabels: Record<string, string> = {
  material_group: "材料组",
  thickness: "厚度",
  diameter: "直径",
  joint: "接头/坡口",
  process: "焊接方法",
  position: "焊接位置",
  filler: "焊材",
  pwht: "PWHT",
  impact: "冲击",
};
const display = (value: unknown) =>
  typeof value === "object" ? JSON.stringify(value) : String(value ?? "-");

const WPSMatching: React.FC = () => {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [revision, setRevision] = useState<RevisionDetail | null>(null);
  const [runs, setRuns] = useState<MatchRow[]>([]);
  const [activeRun, setActiveRun] = useState("");
  const [detail, setDetail] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [jointId, setJointId] = useState("");
  const [selected, setSelected] = useState<MatchRow | null>(null);
  const [confirmForm] = Form.useForm();
  const [gap, setGap] = useState<MatchRow | null>(null);
  const [gapForm] = Form.useForm();
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rev, history] = await Promise.all([
        engineeringService.detail(id),
        matchingService.runs(id),
      ]);
      setRevision(rev);
      setRuns(history);
      setActiveRun((current) => current || history[0]?.id || "");
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (activeRun) void matchingService.detail(activeRun).then(setDetail);
    else setDetail(null);
  }, [activeRun]);
  const jointCandidates = useMemo(
    () => detail?.candidates.filter((x) => x.weld_joint_id === jointId) || [],
    [detail, jointId],
  );
  const joints = revision?.weld_joints || [];
  useEffect(() => {
    if (!jointId && joints.length) setJointId(joints[0].id);
  }, [jointId, joints]);
  const run = async (affectedOnly = false) => {
    setRunning(true);
    try {
      const created = await matchingService.run(id, {
        affected_only: affectedOnly,
        trigger_type: affectedOnly ? "field_change" : "manual",
      });
      message.success(
        `匹配完成：${created.candidate_count} 个候选，${created.gap_count} 个缺口`,
      );
      await load();
      setActiveRun(created.id);
    } finally {
      setRunning(false);
    }
  };
  const confirm = async () => {
    if (!selected) return;
    const values = await confirmForm.validateFields();
    await matchingService.confirm(selected.id, "confirmed", values.note);
    message.success("候选已由工程师确认");
    setSelected(null);
    setDetail(await matchingService.detail(activeRun));
  };
  const reject = async (candidate: MatchRow) => {
    Modal.confirm({
      title: `拒绝 ${candidate.wps_snapshot?.wps_number || "该候选"}`,
      content: "请确认该候选不用于当前焊缝。系统会保留本次人工决定。",
      onOk: async () => {
        await matchingService.confirm(
          candidate.id,
          "rejected",
          "工程师审核拒绝",
        );
        setDetail(await matchingService.detail(activeRun));
      },
    });
  };
  const approve = async () => {
    await matchingService.approve(activeRun, "工程师完成逐焊缝复核");
    message.success("匹配结果已批准，焊缝/WPS/PQR/规则版本已冻结");
    setDetail(await matchingService.detail(activeRun));
    await load();
  };
  const linkGap = async () => {
    if (!gap) return;
    const values = await gapForm.validateFields();
    await matchingService.linkGap(gap.id, values);
    message.success("能力缺口已关联后续计划");
    setGap(null);
    setDetail(await matchingService.detail(activeRun));
  };
  const confirmedCount = new Set(
    detail?.candidates
      .filter((x) => x.confirmation_status === "confirmed")
      .map((x) => x.weld_joint_id),
  ).size;
  const targetCount = detail?.run.target_joint_ids?.length || 0;
  const canApprove =
    detail?.run.status === "completed" &&
    revision?.revision.status === "approved" &&
    targetCount > 0 &&
    confirmedCount === targetCount;
  const criterionColumns = [
    {
      title: "维度",
      dataIndex: "dimension",
      width: 100,
      render: (v: string) => dimensionLabels[v] || v,
    },
    {
      title: "结论",
      dataIndex: "status",
      width: 115,
      render: (v: string) => {
        const meta = statusMeta[v];
        return (
          <Tag color={meta?.color} icon={meta?.icon}>
            {meta?.label || v}
          </Tag>
        );
      },
    },
    { title: "焊缝要求", dataIndex: "required_value", render: display },
    { title: "候选能力", dataIndex: "available_value", render: display },
    { title: "确定性依据", dataIndex: "message" },
  ];
  return (
    <Spin spinning={loading}>
      <div className="matching-page">
        <header className="matching-header">
          <Space align="start">
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(`/engineering/revisions/${id}/review`)}
            />
            <div>
              <Title level={2}>WPS / PQR 自动匹配</Title>
              <Paragraph>
                依据已批准且版本有效的企业能力库逐项计算；推荐排序不能替代工程师确认。
              </Paragraph>
            </div>
          </Space>
          <Space wrap>
            <Button
              icon={<ReloadOutlined />}
              loading={running}
              onClick={() => void run(true)}
            >
              仅重算受影响焊缝
            </Button>
            <Button
              type="primary"
              icon={<SafetyCertificateOutlined />}
              loading={running}
              onClick={() => void run(false)}
            >
              运行全部匹配
            </Button>
          </Space>
        </header>
        <Row gutter={[16, 16]} className="matching-summary">
          <Col xs={12} lg={6}>
            <Card>
              <Text type="secondary">产品版本</Text>
              <Title level={4}>
                V{revision?.revision.revision_number || "-"}
              </Title>
              <Text>数据版本 {revision?.revision.data_version || "-"}</Text>
            </Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card>
              <Text type="secondary">目标焊缝</Text>
              <Title level={4}>{targetCount || joints.length}</Title>
              <Text>本次匹配范围</Text>
            </Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card>
              <Text type="secondary">已人工确认</Text>
              <Title level={4}>
                {confirmedCount} / {targetCount}
              </Title>
              <Progress
                percent={
                  targetCount
                    ? Math.round((confirmedCount / targetCount) * 100)
                    : 0
                }
                showInfo={false}
              />
            </Card>
          </Col>
          <Col xs={12} lg={6}>
            <Card>
              <Text type="secondary">能力缺口</Text>
              <Title level={4}>{detail?.gaps.length || 0}</Title>
              <Text>
                {detail?.run.status === "approved" ? "已冻结" : "等待处置"}
              </Text>
            </Card>
          </Col>
        </Row>
        {!runs.length ? (
          <Card>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="尚未运行匹配"
            >
              <Button type="primary" onClick={() => void run(false)}>
                开始匹配
              </Button>
            </Empty>
          </Card>
        ) : (
          <>
            <Card size="small" className="run-bar">
              <Space wrap>
                <Text strong>匹配运行</Text>
                <Segmented
                  value={activeRun}
                  onChange={(v) => setActiveRun(String(v))}
                  options={runs.slice(0, 5).map((x) => ({
                    value: x.id,
                    label: `${x.status === "approved" ? "已批准" : "运行"} · ${new Date(x.created_at).toLocaleString()}`,
                  }))}
                />
                <Tag
                  color={detail?.run.status === "approved" ? "green" : "blue"}
                >
                  {detail?.run.status === "approved"
                    ? "已批准冻结"
                    : "待工程师确认"}
                </Tag>
              </Space>
            </Card>
            {detail?.run.source_data_version !==
              revision?.revision.data_version && (
              <Alert
                role="alert"
                type="error"
                showIcon
                message="焊缝需求已在本次匹配后变化"
                description="请仅重算受影响焊缝或重新运行全部匹配，旧结果不能批准。"
              />
            )}
            {revision?.revision.status !== "approved" && (
              <Alert
                role="alert"
                type="warning"
                showIcon
                message="产品图纸版本尚未批准"
                description="可以先运行和复核候选，但必须回到图纸审核台批准产品版本后，才能批准并冻结匹配结果。"
              />
            )}
            <div className="matching-workbench">
              <aside>
                <Card title="焊缝清单" size="small">
                  <List
                    dataSource={joints.filter((x) =>
                      detail?.run.target_joint_ids?.includes(x.id),
                    )}
                    renderItem={(joint) => {
                      const rows =
                        detail?.candidates.filter(
                          (x) => x.weld_joint_id === joint.id,
                        ) || [];
                      const confirmed = rows.find(
                        (x) => x.confirmation_status === "confirmed",
                      );
                      return (
                        <List.Item
                          className={
                            jointId === joint.id
                              ? "joint-option active"
                              : "joint-option"
                          }
                          onClick={() => setJointId(joint.id)}
                        >
                          <List.Item.Meta
                            title={joint.weld_number}
                            description={
                              confirmed
                                ? `已确认 ${confirmed.wps_snapshot?.wps_number}`
                                : `${rows.length} 个候选 · 待确认`
                            }
                          />
                          {confirmed ? (
                            <CheckCircleOutlined className="status-ok" />
                          ) : (
                            <ExclamationCircleOutlined className="status-warn" />
                          )}
                        </List.Item>
                      );
                    }}
                  />
                </Card>
              </aside>
              <main>
                <Card
                  title={
                    <Space>
                      <Text strong>候选工艺</Text>
                      <Tag>
                        {
                          revision?.weld_joints.find((x) => x.id === jointId)
                            ?.weld_number
                        }
                      </Tag>
                    </Space>
                  }
                  extra={
                    <Button
                      type="primary"
                      icon={<FileProtectOutlined />}
                      disabled={!canApprove}
                      onClick={() => void approve()}
                    >
                      批准并冻结本次匹配
                    </Button>
                  }
                >
                  {!jointCandidates.length ? (
                    <Empty description="该焊缝没有候选，请处理能力缺口" />
                  ) : (
                    <div className="candidate-list">
                      {jointCandidates.map((candidate) => {
                        const meta = decisionMeta[candidate.decision];
                        return (
                          <Card
                            key={candidate.id}
                            size="small"
                            className={
                              candidate.confirmation_status === "confirmed"
                                ? "candidate-card confirmed"
                                : "candidate-card"
                            }
                            title={
                              <Space>
                                <Text strong>
                                  #{candidate.rank}{" "}
                                  {candidate.wps_snapshot?.wps_number}
                                </Text>
                                {candidate.is_recommended && (
                                  <Tag color="blue">排序优先</Tag>
                                )}
                                <Tag color={meta?.color}>{meta?.label}</Tag>
                              </Space>
                            }
                            extra={
                              <Space>
                                <Text strong>{candidate.score} 分</Text>
                                {candidate.confirmation_status ===
                                "confirmed" ? (
                                  <Tag
                                    color="green"
                                    icon={<CheckCircleOutlined />}
                                  >
                                    工程师已确认
                                  </Tag>
                                ) : (
                                  <>
                                    <Button
                                      disabled={
                                        candidate.decision === "not_eligible" ||
                                        detail?.run.status !== "completed"
                                      }
                                      onClick={() => {
                                        setSelected(candidate);
                                        confirmForm.resetFields();
                                      }}
                                    >
                                      确认
                                    </Button>
                                    <Button
                                      danger
                                      type="text"
                                      disabled={
                                        detail?.run.status !== "completed"
                                      }
                                      onClick={() => void reject(candidate)}
                                    >
                                      拒绝
                                    </Button>
                                  </>
                                )}
                              </Space>
                            }
                          >
                            <Descriptions
                              size="small"
                              column={{ xs: 1, sm: 2, lg: 4 }}
                            >
                              <Descriptions.Item label="WPS版本">
                                {candidate.wps_snapshot?.revision || "-"}
                              </Descriptions.Item>
                              <Descriptions.Item label="PQR">
                                {candidate.pqr_snapshot?.pqr_number || "-"}
                              </Descriptions.Item>
                              <Descriptions.Item label="规则">
                                {candidate.rule_snapshot?.rule_pack_version ||
                                  "-"}
                              </Descriptions.Item>
                              <Descriptions.Item label="确认说明">
                                {candidate.confirmation_note || "-"}
                              </Descriptions.Item>
                            </Descriptions>
                            <Table
                              rowKey="id"
                              size="small"
                              pagination={false}
                              scroll={{ x: 850 }}
                              dataSource={candidate.criteria || []}
                              columns={criterionColumns}
                            />
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </Card>
                <Card title="工艺能力缺口" size="small" className="gap-card">
                  {detail?.gaps.length ? (
                    <List
                      dataSource={detail.gaps.filter(
                        (x) => x.weld_joint_id === jointId,
                      )}
                      renderItem={(item) => (
                        <List.Item
                          actions={[
                            <Button
                              key="link"
                              type="link"
                              icon={<LinkOutlined />}
                              onClick={() => {
                                setGap(item);
                                gapForm.resetFields();
                              }}
                            >
                              关联 pPQR / 新评定计划
                            </Button>,
                          ]}
                        >
                          <List.Item.Meta
                            avatar={
                              <CloseCircleOutlined
                                className={
                                  item.severity === "blocking"
                                    ? "status-error"
                                    : "status-warn"
                                }
                              />
                            }
                            title={item.message}
                            description={
                              item.status === "linked"
                                ? `已关联：${item.qualification_plan_reference || `pPQR #${item.linked_ppqr_id}`}`
                                : "尚未处理"
                            }
                          />
                        </List.Item>
                      )}
                    />
                  ) : (
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description="当前焊缝没有能力缺口"
                    />
                  )}
                </Card>
              </main>
            </div>
          </>
        )}
        <Drawer
          title="工程师确认候选"
          width={460}
          open={!!selected}
          onClose={() => setSelected(null)}
          extra={
            <Button type="primary" onClick={() => void confirm()}>
              确认选择
            </Button>
          }
        >
          <Alert
            type="warning"
            showIcon
            message="人工确认是必需步骤"
            description="规则边界或信息不足的候选必须填写复核依据；确认后仍需批准整个匹配运行。"
          />
          <Descriptions
            column={1}
            bordered
            size="small"
            className="confirm-description"
          >
            <Descriptions.Item label="WPS">
              {selected?.wps_snapshot?.wps_number}
            </Descriptions.Item>
            <Descriptions.Item label="PQR">
              {selected?.pqr_snapshot?.pqr_number}
            </Descriptions.Item>
            <Descriptions.Item label="匹配结论">
              {decisionMeta[selected?.decision || ""]?.label}
            </Descriptions.Item>
          </Descriptions>
          <Form form={confirmForm} layout="vertical">
            <Form.Item
              name="note"
              label="确认依据"
              rules={[
                {
                  required: selected?.decision === "needs_confirmation",
                  message: "边界或信息不足候选必须填写确认依据",
                },
              ]}
            >
              <Input.TextArea
                rows={5}
                placeholder="填写复核的标准条款、实测数据或工程判断依据"
              />
            </Form.Item>
          </Form>
        </Drawer>
        <Modal
          title="关联能力补齐计划"
          open={!!gap}
          onCancel={() => setGap(null)}
          onOk={() => void linkGap()}
        >
          <Form form={gapForm} layout="vertical">
            <Form.Item name="ppqr_id" label="关联现有 pPQR">
              <InputNumber
                min={1}
                style={{ width: "100%" }}
                placeholder="填写 pPQR ID（可选）"
              />
            </Form.Item>
            <Form.Item
              name="qualification_plan_reference"
              label="新评定计划编号"
            >
              <Input placeholder="如：QP-2026-018（与 pPQR 二选一）" />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </Spin>
  );
};
export default WPSMatching;
