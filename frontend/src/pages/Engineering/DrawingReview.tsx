import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Checkbox,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Spin,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  FileSearchOutlined,
  MergeCellsOutlined,
  PlusOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  ScissorOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import {
  DataRow,
  engineeringService,
  RevisionDetail,
} from "@/services/engineering";
import smartImportService from "@/services/smartImport";
import { usePreferencesStore } from "@/store/preferencesStore";
import {
  AI_DATA_OUTBOUND_NOTICE_VERSION,
  aiDataOutboundNotice,
  hasPersistentAIDataAuthorization,
} from "@/utils/aiPrivacy";
import "./engineering.css";

const { Title, Text } = Typography;

const sha256Hex = async (value: string) => {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
};

const DrawingReview: React.FC = () => {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const preferences = usePreferencesStore((state) => state.preferences);
  const persistentOutboundAuthorization =
    hasPersistentAIDataAuthorization(preferences);
  const [detail, setDetail] = useState<RevisionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [parseJob, setParseJob] = useState<DataRow | null>(null);
  const [pollFailed, setPollFailed] = useState(false);
  const parseSubmitting = useRef(false);
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const [privacyConfirmed, setPrivacyConfirmed] = useState(false);
  const [productOpen, setProductOpen] = useState(false);
  const [platformHost, setPlatformHost] = useState("");
  const [platformRoute, setPlatformRoute] = useState("");
  const [page, setPage] = useState(1);
  const [preview, setPreview] = useState("");
  const [focus, setFocus] = useState<DataRow | null>(null);
  const [edit, setEdit] = useState<{
    type: "part" | "joint" | "requirement";
    row: DataRow;
  } | null>(null);
  const [editForm] = Form.useForm();
  const [productForm] = Form.useForm();
  const [jointForm] = Form.useForm();
  const [jointOpen, setJointOpen] = useState(false);
  const [selected, setSelected] = useState<React.Key[]>([]);
  const [history, setHistory] = useState<DataRow[]>([]);
  const drawingPaneRef = useRef<HTMLElement | null>(null);
  const [acceptingId, setAcceptingId] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDetail(await engineeringService.detail(id));
      setHistory(await engineeringService.history(id));
      const jobs = await engineeringService.parseJobs(id);
      setParseJob(jobs[0] || null);
      setParsing(["queued", "processing"].includes(jobs[0]?.status));
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => {
    void load();
    void smartImportService
      .getAICapabilities({ task_type: "drawing_import", complexity: "advanced" })
      .then((value) => {
        setPlatformHost(value.platform_available ? value.platform_host : "");
        setPlatformRoute(value.platform_route || "");
      }).catch(() => setPlatformHost(""));
  }, [load]);
  useEffect(() => {
    if (!parseJob || !["queued", "processing"].includes(parseJob.status)) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const jobs = await engineeringService.parseJobs(id);
        if (cancelled) return;
        setPollFailed(false);
        const latest = jobs[0] || null;
        setParseJob(latest);
        if (!latest || !["queued", "processing"].includes(latest.status)) {
          setParsing(false);
          if (latest?.status === "completed") message.success("图纸解析完成，请逐项核对");
          await load();
        }
      } catch {
        if (!cancelled) {
          setPollFailed(true);
          setParseJob({ ...parseJob });
        }
      }
    }, pollFailed ? 10000 : 2500);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [id, load, parseJob, pollFailed]);
  useEffect(() => {
    let url = "";
    void engineeringService.preview(id, page).then((blob) => {
      url = URL.createObjectURL(blob);
      setPreview((old) => {
        if (old) URL.revokeObjectURL(old);
        return url;
      });
    });
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [id, page]);
  const evidence = focus?.evidence || {};
  useEffect(() => {
    if (evidence.page && evidence.page !== page) setPage(evidence.page);
  }, [evidence.page, page]);
  const box = useMemo(() => {
    const b = evidence.bbox;
    return Array.isArray(b) && b.length === 4
      ? {
          left: `${b[0] * 100}%`,
          top: `${b[1] * 100}%`,
          width: `${(b[2] - b[0]) * 100}%`,
          height: `${(b[3] - b[1]) * 100}%`,
        }
      : null;
  }, [evidence]);
  const readonly =
    detail?.revision.status === "approved" ||
    detail?.revision.status === "superseded";
  const runAI = () => {
    if (persistentOutboundAuthorization) {
      void confirmRunAI();
      return;
    }
    setPrivacyConfirmed(false);
    setPrivacyOpen(true);
  };
  const confirmRunAI = async () => {
    if (parseSubmitting.current || parsing) return;
    if (!detail?.revision.drawing_document_id || !platformHost) {
      message.error("无法识别图纸文档或外部模型服务域名");
      return;
    }
    parseSubmitting.current = true;
    setParsing(true);
    try {
      const notice = aiDataOutboundNotice(platformHost);
      const consent = await smartImportService.createOutboundConsent({
        document_id: detail.revision.drawing_document_id,
        provider_host: platformHost,
        purpose: `识别图纸 ${detail.revision.drawing_filename || id}`,
        privacy_notice_version: AI_DATA_OUTBOUND_NOTICE_VERSION,
        privacy_notice_hash: await sha256Hex(notice),
        authorized: true,
      });
      const result = await engineeringService.parse(id, {
        mode: "platform",
        run_ocr: true,
        outbound_consent_id: consent.id,
        expected_platform_route: platformRoute || undefined,
      });
      setParseJob(result.job);
      setPrivacyOpen(false);
      message.info("图纸已进入后台识别，可离开页面后返回查看");
    } catch {
      // The shared API layer displays one normalized error message.
      setParsing(false);
    } finally {
      parseSubmitting.current = false;
    }
  };
  const openEdit = (type: "part" | "joint" | "requirement", row: DataRow) => {
    setEdit({ type, row });
    editForm.setFieldsValue(row);
    setFocus(row);
  };
  const saveEdit = async () => {
    if (!edit) return;
    const values = await editForm.validateFields();
    if (edit.type === "part")
      await engineeringService.patchPart(edit.row.id, values);
    else if (edit.type === "joint")
      await engineeringService.patchJoint(edit.row.id, values);
    else await engineeringService.patchRequirement(edit.row.id, values);
    message.success("修正已保存，相关匹配/焊序/定额结果已局部失效");
    setEdit(null);
    await load();
  };
  const openProductIdentity = () => {
    const product = detail?.revision.drawing_metadata?.extracted_product || {};
    productForm.setFieldsValue({
      drawing_number: product.drawing_number,
      product_name: product.product_name,
    });
    setProductOpen(true);
  };
  const saveProductIdentity = async () => {
    const values = await productForm.validateFields();
    await engineeringService.patchProductIdentity(id, values);
    message.success("图签信息已人工补录");
    setProductOpen(false);
    await load();
  };
  const accept = async (
    type: "part" | "joint" | "requirement",
    row: DataRow,
  ) => {
    const fn =
      type === "part"
        ? engineeringService.patchPart
        : type === "joint"
          ? engineeringService.patchJoint
          : engineeringService.patchRequirement;
    setAcceptingId(row.id);
    try {
      await fn(row.id, { review_status: "accepted" });
      message.success(`已接受${type === "joint" ? "焊缝" : type === "part" ? "零部件" : "焊接要求"}识别结果`);
      await load();
    } catch {
      // API interceptor presents the server reason once; avoid a duplicate toast.
    } finally {
      setAcceptingId("");
    }
  };
  const locateEvidence = (row: DataRow) => {
    const itemEvidence = row.evidence || {};
    setFocus(row);
    if (itemEvidence.page) setPage(itemEvidence.page);
    drawingPaneRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (!itemEvidence.page) {
      message.info("该字段没有可用的证据页码；已显示证据原文，可使用“修正”人工确认");
    } else if (!itemEvidence.bbox?.length) {
      message.info(`已切换到第 ${itemEvidence.page} 页；模型未返回框选坐标`);
    }
  };
  const addJoint = async () => {
    const values = await jointForm.validateFields();
    await engineeringService.addJoint(id, values);
    message.success("焊缝已新增");
    setJointOpen(false);
    jointForm.resetFields();
    await load();
  };
  const split = async (row: DataRow) => {
    Modal.confirm({
      title: `拆分焊缝 ${row.weld_number}`,
      content: (
        <Text>
          将拆分为 {row.weld_number}-1 和 {row.weld_number}
          -2，长度均分；完成后可继续修正。
        </Text>
      ),
      onOk: async () => {
        await engineeringService.splitJoint(row.id, {
          weld_numbers: [`${row.weld_number}-1`, `${row.weld_number}-2`],
        });
        await load();
      },
    });
  };
  const merge = async () => {
    if (selected.length < 2) return message.warning("请选择至少两条焊缝");
    await engineeringService.mergeJoints(id, {
      joint_ids: selected,
      weld_number: `M-${Date.now().toString().slice(-6)}`,
    });
    message.success("焊缝已合并，请修正新编号");
    setSelected([]);
    await load();
  };
  const approve = async () => {
    await engineeringService.approve(id);
    message.success("产品图纸版本已批准并锁定");
    await load();
  };
  const riskCount = detail?.validation.risks.length || 0;
  const sourceColumn = {
    title: "来源",
    width: 105,
    render: (_: unknown, row: DataRow) => {
      const source = row.evidence?.source;
      if (source === "manual_entry") return <Tag color="blue">人工新增</Tag>;
      if (source === "manual_correction" || row.review_status === "corrected")
        return <Tag color="purple">人工修正</Tag>;
      return <Tag color="cyan">AI 图纸提取</Tag>;
    },
  };
  const partColumns = [
    { title: "件号", dataIndex: "part_number", width: 90 },
    { title: "零部件", dataIndex: "name" },
    { title: "材料", dataIndex: "material_spec" },
    { title: "厚度 mm", dataIndex: "thickness_mm", width: 90 },
    sourceColumn,
    {
      title: "状态",
      dataIndex: "review_status",
      width: 85,
      render: (v: string) => (
        <Tag color={v === "pending" ? "orange" : "green"}>
          {v === "pending" ? "待审核" : v === "accepted" ? "已接受" : "已修正"}
        </Tag>
      ),
    },
    {
      title: "操作",
      width: 145,
      render: (_: unknown, r: DataRow) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => locateEvidence(r)}
          >
            定位
          </Button>
          {!readonly && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                loading={acceptingId === r.id}
                title="接受识别结果"
                onClick={() => void accept("part", r)}
              />
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => openEdit("part", r)}
              />
            </>
          )}
        </Space>
      ),
    },
  ];
  const jointColumns = [
    { title: "焊缝号", dataIndex: "weld_number", width: 100 },
    { title: "接头", dataIndex: "joint_type", width: 90 },
    { title: "坡口", dataIndex: "groove_type", width: 90 },
    { title: "长度 mm", dataIndex: "length_mm", width: 90 },
    sourceColumn,
    {
      title: "置信度",
      dataIndex: "confidence",
      width: 85,
      render: (v: number) => (
        <Badge
          status={v >= 0.8 ? "success" : v >= 0.6 ? "warning" : "error"}
          text={v == null ? "-" : `${Math.round(v * 100)}%`}
        />
      ),
    },
    {
      title: "状态",
      dataIndex: "review_status",
      width: 85,
      render: (v: string) => (
        <Tag color={v === "pending" ? "orange" : "green"}>
          {v === "pending" ? "待审核" : v === "accepted" ? "已接受" : "已修正"}
        </Tag>
      ),
    },
    {
      title: "操作",
      width: 220,
      render: (_: unknown, r: DataRow) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => locateEvidence(r)}
          >
            定位
          </Button>
          {!readonly && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                loading={acceptingId === r.id}
                title="接受识别结果"
                onClick={() => void accept("joint", r)}
              />
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => openEdit("joint", r)}
              />
              <Button
                type="link"
                size="small"
                icon={<ScissorOutlined />}
                onClick={() => void split(r)}
              />
              <Popconfirm
                title="删除这条焊缝？"
                onConfirm={async () => {
                  await engineeringService.deleteJoint(r.id);
                  await load();
                }}
              >
                <Button
                  danger
                  type="link"
                  size="small"
                  icon={<DeleteOutlined />}
                />
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];
  const reqColumns = [
    {
      title: "焊缝号",
      dataIndex: "weld_joint_id",
      render: (v: string) =>
        detail?.weld_joints.find((x) => x.id === v)?.weld_number || "总体要求",
    },
    { title: "焊接方法", dataIndex: "welding_process" },
    { title: "材料组", dataIndex: "material_group" },
    {
      title: "直径 mm",
      dataIndex: "diameter_mm",
      render: (v: number, row: DataRow) =>
        row.diameter_applicable === false ? "不适用" : (v ?? "待确认"),
    },
    {
      title: "焊材",
      render: (_: unknown, row: DataRow) =>
        [row.filler_material_spec, row.filler_material_classification]
          .filter(Boolean)
          .join(" / ") || "待确认",
    },
    {
      title: "无损检测",
      dataIndex: "nde_methods",
      render: (v: string[]) => (v || []).join(" / ") || "-",
    },
    { title: "比例", dataIndex: "nde_rate" },
    {
      title: "PWHT",
      dataIndex: "pwht_required",
      render: (v: boolean) => (v == null ? "-" : v ? "需要" : "不需要"),
    },
    {
      title: "冲击",
      dataIndex: "impact_required",
      render: (v: boolean) => (v == null ? "-" : v ? "需要" : "不需要"),
    },
    { title: "特殊要求", dataIndex: "special_requirements" },
    sourceColumn,
    {
      title: "操作",
      width: 120,
      render: (_: unknown, r: DataRow) => (
        <Space>
          <Button type="link" size="small" onClick={() => locateEvidence(r)}>
            定位
          </Button>
          {!readonly && (
            <Button
              type="link"
              size="small"
              onClick={() => openEdit("requirement", r)}
            >
              修正
            </Button>
          )}
        </Space>
      ),
    },
  ];
  return (
    <Spin spinning={loading}>
      <div className="drawing-review">
        {parseJob && <Alert showIcon style={{ marginBottom: 16 }}
          type={parseJob.status === "failed" || parseJob.status === "cancelled" ? "error" : "info"}
          message={parseJob.status === "completed" ? "识别完成，结果须人工核对" :
            parseJob.status === "failed" || parseJob.status === "cancelled" ? "识别未完成，可重新提交" :
              `后台识别中 · ${parseJob.progress || 0}%`}
          description={pollFailed ? "暂时无法获取进度，正在重试；后台任务仍会继续。" :
            parseJob.error_message || ({ queued: "等待后台处理", rendering: "渲染页面", title: "识别图签", parts: "识别零件", welds: "识别焊缝", validating: "校验并保存" } as Record<string, string>)[parseJob.progress_detail?.phase] || "请逐项核对图签、零件、焊缝和证据位置。"}
        />}
        <div className="review-header">
          <Space>
            <Button
              icon={<SafetyCertificateOutlined />}
              onClick={() => navigate(`/engineering/revisions/${id}/matching`)}
            >
              WPS/PQR 匹配
            </Button>
            <Button
              onClick={() => navigate(`/engineering/revisions/${id}/sequence`)}
            >
              焊序编排
            </Button>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate("/engineering")}
            />
            <div>
              <Title level={3}>
                {detail?.revision.drawing_filename || "图纸审核台"}
              </Title>
              <Space>
                <Tag>V{detail?.revision.revision_number}</Tag>
                <Tag
                  color={
                    detail?.revision.status === "approved" ? "green" : "orange"
                  }
                >
                  {detail?.revision.status === "approved" ? "已批准" : "待审核"}
                </Tag>
                <Text type="secondary">
                  数据版本 {detail?.revision.data_version}
                </Text>
              </Space>
            </div>
          </Space>
          <Space>
            <Button
              icon={<RobotOutlined />}
              loading={parsing}
              disabled={readonly}
              onClick={() => void runAI()}
            >
              AI 识别图纸
            </Button>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              disabled={readonly || !detail?.validation.can_approve}
              onClick={() => void approve()}
            >
              批准版本
            </Button>
          </Space>
        </div>
        <Modal
          title="确认向外部模型发送图纸"
          open={privacyOpen}
          onCancel={() => !parsing && setPrivacyOpen(false)}
          onOk={() => void confirmRunAI()}
          okText="确认并开始识别"
          okButtonProps={{ disabled: !privacyConfirmed || !platformHost }}
          confirmLoading={parsing}
        >
          <Alert
            type="warning"
            showIcon
            message={`数据接收方：${platformHost || "尚未配置"}`}
              description={platformHost
                ? aiDataOutboundNotice(platformHost)
                : "管理员模型配置未提供可用服务域名。"}
          />
          <Checkbox
            style={{ marginTop: 16 }}
            checked={privacyConfirmed}
            disabled={!platformHost}
            onChange={(event) => setPrivacyConfirmed(event.target.checked)}
          >
            我已阅读并确认该图纸允许发送至上述外部模型服务
          </Checkbox>
        </Modal>
        {riskCount > 0 && (
          <Alert
            type={detail?.validation.can_approve ? "warning" : "error"}
            showIcon
            icon={<WarningOutlined />}
            message={`发现 ${riskCount} 项审核风险`}
            description="关键字段保持空白等待人工确认；完成修正后才可批准。"
          />
        )}
        <div className="review-workbench">
          <section className="drawing-pane" ref={drawingPaneRef}>
            <Card
              size="small"
              title={
                <Space>
                  <FileSearchOutlined />
                  图纸证据
                </Space>
              }
              extra={
                <Space>
                  <Button
                    disabled={page <= 1}
                    onClick={() => setPage((v) => v - 1)}
                  >
                    上一页
                  </Button>
                  <Text>
                    {page} / {detail?.revision.drawing_page_count || 1}
                  </Text>
                  <Button
                    disabled={
                      page >= (detail?.revision.drawing_page_count || 1)
                    }
                    onClick={() => setPage((v) => v + 1)}
                  >
                    下一页
                  </Button>
                </Space>
              }
            >
              <div className="drawing-canvas">
                {preview ? (
                  <>
                    <img src={preview} alt={`图纸第 ${page} 页`} />
                    {box && (
                      <div className="drawing-evidence-box" style={box} />
                    )}
                  </>
                ) : (
                  <Empty description="图纸预览加载中" />
                )}
              </div>
              {evidence.text && (
                <Alert
                  type="info"
                  message="识别证据"
                  description={evidence.text}
                />
              )}
            </Card>
          </section>
          <section className="data-pane">
            <Card size="small">
              <Descriptions size="small" column={3}>
                <Descriptions.Item label="解析状态">
                  {detail?.revision.parse_status}
                </Descriptions.Item>
                <Descriptions.Item label="零部件">
                  {detail?.parts.length || 0}
                </Descriptions.Item>
                <Descriptions.Item label="焊缝">
                  {detail?.weld_joints.length || 0}
                </Descriptions.Item>
              </Descriptions>
            </Card>
            <Card
              size="small"
              title="图签信息"
              extra={!readonly && <Button icon={<EditOutlined />} onClick={openProductIdentity}>人工补录</Button>}
            >
              <Descriptions size="small" column={2}>
                <Descriptions.Item label="图号">
                  {detail?.revision.drawing_metadata?.extracted_product?.drawing_number || <Text type="danger">待补录</Text>}
                  <Tag style={{ marginLeft: 8 }} color={detail?.revision.drawing_metadata?.extracted_product?.field_sources?.drawing_number === "manual_correction" ? "purple" : "cyan"}>
                    {detail?.revision.drawing_metadata?.extracted_product?.field_sources?.drawing_number === "manual_correction" ? "人工修正" : "AI 图纸提取"}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="产品名称">
                  {detail?.revision.drawing_metadata?.extracted_product?.product_name || <Text type="danger">待补录</Text>}
                  <Tag style={{ marginLeft: 8 }} color={detail?.revision.drawing_metadata?.extracted_product?.field_sources?.product_name === "manual_correction" ? "purple" : "cyan"}>
                    {detail?.revision.drawing_metadata?.extracted_product?.field_sources?.product_name === "manual_correction" ? "人工修正" : "AI 图纸提取"}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>
            <Tabs
              items={[
                {
                  key: "joints",
                  label: `焊缝 (${detail?.weld_joints.length || 0})`,
                  children: (
                    <>
                      <Space className="review-actions">
                        <Button
                          icon={<PlusOutlined />}
                          disabled={readonly}
                          onClick={() => setJointOpen(true)}
                        >
                          新增
                        </Button>
                        <Button
                          icon={<MergeCellsOutlined />}
                          disabled={readonly || selected.length < 2}
                          onClick={() => void merge()}
                        >
                          合并所选
                        </Button>
                      </Space>
                      <Table
                        size="small"
                        rowKey="id"
                        scroll={{ x: 980 }}
                        pagination={false}
                        dataSource={detail?.weld_joints || []}
                        columns={jointColumns}
                        rowSelection={
                          readonly
                            ? undefined
                            : {
                                selectedRowKeys: selected,
                                onChange: setSelected,
                              }
                        }
                        onRow={(r) => ({ onClick: () => setFocus(r) })}
                      />
                    </>
                  ),
                },
                {
                  key: "parts",
                  label: `零部件 (${detail?.parts.length || 0})`,
                  children: (
                    <Table
                      size="small"
                      rowKey="id"
                      pagination={false}
                      dataSource={detail?.parts || []}
                      columns={partColumns}
                      onRow={(r) => ({ onClick: () => setFocus(r) })}
                    />
                  ),
                },
                {
                  key: "requirements",
                  label: "技术要求",
                  children: (
                    <Table
                      size="small"
                      rowKey="id"
                      pagination={false}
                      dataSource={detail?.requirements || []}
                      columns={reqColumns}
                    />
                  ),
                },
                {
                  key: "risks",
                  label: (
                    <Badge count={riskCount} size="small">
                      审核风险
                    </Badge>
                  ),
                  children: (
                    <div className="risk-list">
                      {detail?.validation.risks.length ? (
                        detail.validation.risks.map((r, i) => (
                          <Alert
                            key={i}
                            type={
                              r.severity === "critical" ? "error" : "warning"
                            }
                            showIcon
                            message={r.message}
                          />
                        ))
                      ) : (
                        <Empty description="未发现风险" />
                      )}
                    </div>
                  ),
                },
                {
                  key: "history",
                  label: "审核记录",
                  children: (
                    <Table
                      size="small"
                      rowKey="id"
                      pagination={false}
                      dataSource={history}
                      columns={[
                        {
                          title: "时间",
                          dataIndex: "created_at",
                          render: (v) => new Date(v).toLocaleString(),
                        },
                        { title: "动作", dataIndex: "action" },
                        { title: "对象", dataIndex: "entity_type" },
                        { title: "原因", dataIndex: "reason" },
                      ]}
                    />
                  ),
                },
              ]}
            />
          </section>
        </div>
        <Drawer
          title="字段接受 / 修正"
          width={440}
          open={!!edit}
          onClose={() => setEdit(null)}
          extra={
            <Button type="primary" onClick={() => void saveEdit()}>
              保存修正
            </Button>
          }
        >
          <Form form={editForm} layout="vertical">
            {edit?.type === "part" ? (
              <>
                <Form.Item name="part_number" label="件号">
                  <Input />
                </Form.Item>
                <Form.Item
                  name="name"
                  label="名称"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
                <Form.Item name="material_spec" label="材料牌号">
                  <Input />
                </Form.Item>
                <Form.Item name="thickness_mm" label="厚度 mm">
                  <InputNumber min={0} style={{ width: "100%" }} />
                </Form.Item>
              </>
            ) : edit?.type === "joint" ? (
              <>
                <Form.Item
                  name="weld_number"
                  label="焊缝编号"
                  rules={[{ required: true }]}
                >
                  <Input />
                </Form.Item>
                <Form.Item name="joint_type" label="接头形式">
                  <Input />
                </Form.Item>
                <Form.Item name="part_a_id" label="连接零部件 A" rules={[{ required: true, message: "请选择零部件 A" }]}>
                  <Select
                    showSearch
                    optionFilterProp="label"
                    options={(detail?.parts || []).map((part) => ({
                      value: part.id,
                      label: `${part.part_number || "无件号"} · ${part.name}`,
                    }))}
                  />
                </Form.Item>
                <Form.Item name="part_b_id" label="连接零部件 B" rules={[{ required: true, message: "请选择零部件 B" }]}>
                  <Select
                    showSearch
                    optionFilterProp="label"
                    options={(detail?.parts || []).map((part) => ({
                      value: part.id,
                      label: `${part.part_number || "无件号"} · ${part.name}`,
                    }))}
                  />
                </Form.Item>
                <Form.Item name="groove_type" label="坡口形式">
                  <Input />
                </Form.Item>
                <Form.Item name="length_mm" label="长度 mm">
                  <InputNumber min={0} style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item name="weld_position" label="焊接位置">
                  <Input />
                </Form.Item>
              </>
            ) : (
              <>
                <Form.Item name="welding_process" label="焊接方法">
                  <Input placeholder="如 GTAW、SMAW" />
                </Form.Item>
                <Form.Item
                  name="material_group"
                  label="材料组（明确要求时填写）"
                >
                  <Input />
                </Form.Item>
                <Form.Item name="diameter_applicable" label="是否适用直径评定">
                  <Select
                    allowClear
                    options={[
                      { value: true, label: "适用（管件/筒体）" },
                      { value: false, label: "不适用（板件）" },
                    ]}
                  />
                </Form.Item>
                <Form.Item name="diameter_mm" label="直径 mm">
                  <InputNumber min={0} style={{ width: "100%" }} />
                </Form.Item>
                <Form.Item name="filler_material_spec" label="焊材标准">
                  <Input />
                </Form.Item>
                <Form.Item
                  name="filler_material_classification"
                  label="焊材分类"
                >
                  <Input />
                </Form.Item>
                <Form.Item name="nde_methods" label="无损检测方法">
                  <Select mode="tags" />
                </Form.Item>
                <Form.Item name="nde_rate" label="检测比例">
                  <Input />
                </Form.Item>
                <Form.Item name="pwht_required" label="焊后热处理">
                  <Select
                    options={[
                      { value: true, label: "需要" },
                      { value: false, label: "不需要" },
                    ]}
                  />
                </Form.Item>
                <Form.Item name="impact_required" label="冲击试验">
                  <Select
                    options={[
                      { value: true, label: "需要" },
                      { value: false, label: "不需要" },
                    ]}
                  />
                </Form.Item>
                <Form.Item name="special_requirements" label="特殊要求">
                  <Input.TextArea rows={4} />
                </Form.Item>
              </>
            )}
          </Form>
        </Drawer>
        <Modal
          title="人工补录图签信息"
          open={productOpen}
          onCancel={() => setProductOpen(false)}
          onOk={() => void saveProductIdentity()}
          okText="保存补录"
        >
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message="AI 已识别的零部件、焊缝和技术要求会继续保留"
            description="这里只补充图号和产品名称，不会重新调用模型或覆盖其他识别结果。"
          />
          <Form form={productForm} layout="vertical">
            <Form.Item name="drawing_number" label="图号" rules={[{ required: true, message: "请输入图号" }]}>
              <Input maxLength={120} />
            </Form.Item>
            <Form.Item name="product_name" label="产品名称" rules={[{ required: true, message: "请输入产品名称" }]}>
              <Input maxLength={200} />
            </Form.Item>
          </Form>
        </Modal>
        <Modal
          title="人工新增焊缝"
          open={jointOpen}
          onCancel={() => setJointOpen(false)}
          onOk={() => void addJoint()}
        >
          <Form form={jointForm} layout="vertical">
            <Form.Item
              name="weld_number"
              label="焊缝编号"
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>
            <Form.Item name="joint_type" label="接头形式">
              <Input />
            </Form.Item>
            <Form.Item name="groove_type" label="坡口形式">
              <Input />
            </Form.Item>
            <Form.Item name="length_mm" label="长度 mm">
              <InputNumber min={0} style={{ width: "100%" }} />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </Spin>
  );
};
export default DrawingReview;
