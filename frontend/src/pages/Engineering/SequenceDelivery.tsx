import { useEffect, useRef, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  QRCode,
  Select,
  Space,
  Spin,
  Table,
  Typography,
  message,
} from "antd";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { productionReleaseService } from "@/services/productionRelease";
import ProductionReleasePanel from "./ProductionReleasePanel";
import SourceImpactAlert from "./SourceImpactAlert";
import "./delivery.css";

type Row = Record<string, any>;
const labels: Record<string, string> = {
  pending: "待执行",
  in_progress: "执行中",
  completed: "已完成",
  cancelled: "已取消",
  recorded: "过程记录",
  pass: "合格",
  fail: "不合格",
};
const parameterLabels: Record<string, string> = {
  current: "电流 (A)",
  voltage: "电压 (V)",
  travel_speed: "焊速 (mm/min)",
  heat_input: "热输入 (kJ/mm)",
  preheat_temperature: "预热温度 (℃)",
  interpass_temperature: "层间温度 (℃)",
};
const parametersText = (value: Row | undefined) =>
  Object.entries(value || {})
    .map(([key, value]) => `${parameterLabels[key] || key}：${value}`)
    .join("；") || "未记录";
const inspectionText = (value: Row | undefined) =>
  !value || !Object.keys(value).length
    ? "无单独检验要求"
    : [
        value.methods?.join("、"),
        value.rate && `比例 ${value.rate}`,
        value.stage && `阶段 ${value.stage}`,
        value.timing && (value.timing === "before" ? "热处理前" : "热处理后"),
        value.type === "heat_treatment_record" && "热处理记录核验",
      ]
        .filter(Boolean)
        .join(" · ") || valueText(value);
const valueText = (value: unknown) =>
  value == null
    ? "未记录"
    : typeof value === "object"
      ? JSON.stringify(value)
      : String(value);

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function SequenceDelivery() {
  const { sequenceId = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);
  const report = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setData(null);
    setError("");
    productionReleaseService
      .delivery(sequenceId)
      .then((value) => {
        if (active) setData(value);
      })
      .catch(() => {
        if (active)
          setError(
            "交付包加载失败，版本可能未放行或当前工作区无权访问。请切换到所属工作区后重试。",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [sequenceId, reload]);
  const joints: Row[] = data?.drawing?.weld_joints || [];
  const jointId = params.get("joint");
  const taskId = params.get("task");
  const tasks: Row[] = (data?.tasks || [])
    .filter(
      (task: Row) =>
        (!taskId || String(task.id) === taskId) &&
        (!jointId ||
          !task.source_weld_joint_id ||
          task.source_weld_joint_id === jointId ||
          task.source_step_snapshot?.process_parameters?.affected_joint_ids?.includes(
            jointId,
          )),
    )
    .sort(
      (a: Row, b: Row) =>
        a.source_step_snapshot.order_index - b.source_step_snapshot.order_index,
    );
  const linkFor = (task: Row) =>
    `${window.location.origin}/engineering/sequences/${sequenceId}/delivery?task=${task.id}${task.source_weld_joint_id ? `&joint=${encodeURIComponent(task.source_weld_joint_id)}` : ""}`;
  const exportHtml = () => {
    if (!report.current) return;
    const clone = report.current.cloneNode(true) as HTMLElement;
    clone
      .querySelectorAll(".delivery-no-print,button")
      .forEach((node) => node.remove());
    clone.querySelectorAll("a").forEach((node) => {
      node.href = new URL(
        node.getAttribute("href") || "",
        window.location.origin,
      ).href;
    });
    const css = Array.from(document.styleSheets)
      .flatMap((sheet) => {
        try {
          return Array.from(sheet.cssRules).map((rule) => rule.cssText);
        } catch {
          return [];
        }
      })
      .join("\n");
    download(
      new Blob(
        [
          `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:"><title>施工交付包</title><style>${css.replace(/<\/style/gi, "<\\/style")}</style><body>${clone.outerHTML}</body></html>`,
        ],
        { type: "text/html;charset=utf-8" },
      ),
      `施工交付包-${sequenceId}.html`,
    );
    message.success("已导出当前筛选范围的交付包，可离线查看或打印");
  };
  return (
    <Spin spinning={loading}>
      <div className="delivery-page">
        <Space wrap className="delivery-no-print">
          <Button onClick={() => setReload((value) => value + 1)}>
            刷新交付记录
          </Button>
          <Button disabled={!data} onClick={exportHtml}>
            导出可打印 HTML
          </Button>
          <Button
            disabled={!data}
            onClick={() =>
              download(
                new Blob([JSON.stringify(data, null, 2)], {
                  type: "application/json",
                }),
                `施工交付数据-${sequenceId}.json`,
              )
            }
          >
            导出完整数据
          </Button>
          <Button disabled={!data} onClick={() => window.print()}>
            打印
          </Button>
          <Select
            aria-label="按焊缝定位"
            allowClear
            value={jointId || undefined}
            style={{ minWidth: 200 }}
            placeholder="全部焊缝"
            options={joints.map((j) => ({ value: j.id, label: j.weld_number }))}
            onChange={(value) => setParams(value ? { joint: value } : {})}
          />
          {taskId && (
            <Button
              onClick={() => setParams(jointId ? { joint: jointId } : {})}
            >
              查看该焊缝全部工序
            </Button>
          )}
        </Space>
        {error && <Alert type="error" message={error} />}
        {data && (
          <>
            <div ref={report} className="delivery-report">
              <Typography.Title level={2}>施工交付包</Typography.Title>
              <Alert type="info" message={data.notice} />
              <SourceImpactAlert
                impact={data.source_impact}
                revisionId={data.release.product_revision_id}
              />
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="发布批次">
                  {data.release.id}
                </Descriptions.Item>
                <Descriptions.Item label="生成时间">
                  {data.generated_at}
                </Descriptions.Item>
                <Descriptions.Item label="图纸">
                  {data.drawing?.filename || "旧批次未保存图纸位置快照"}
                </Descriptions.Item>
                <Descriptions.Item label="冻结版本">
                  {data.release.sequence_frozen_hash}
                </Descriptions.Item>
              </Descriptions>
              {tasks.length === 0 && (
                <Empty description="当前筛选未找到施工任务" />
              )}
              {tasks.map((task) => {
                const step = task.source_step_snapshot || {};
                const joint = joints.find(
                  (j) => j.id === task.source_weld_joint_id,
                );
                const evidence = joint?.evidence || {};
                const process = step.process_parameters || {};
                const prerequisites = (data.frozen_sequence.dependencies || [])
                  .filter(
                    (edge: Row) =>
                      edge.successor_code === step.step_code &&
                      edge.is_mandatory !== false,
                  )
                  .map((edge: Row) => edge.predecessor_code);
                const inspections = (data.inspections || []).filter(
                  (i: Row) => i.production_task_id === task.id,
                );
                const traces = (data.executions || []).filter(
                  (t: Row) => t.production_task_id === task.id,
                );
                return (
                  <Card
                    key={task.id}
                    className="delivery-task"
                    title={`${step.order_index}. ${task.task_name}`}
                    id={`task-${task.id}`}
                  >
                    <div className="delivery-task-head">
                      <div>
                        <div>
                          步骤：{step.step_code} · 状态：
                          {labels[task.status] || task.status}
                        </div>
                        <div>
                          焊缝：{joint?.weld_number || "公共工序"} · 原图页：
                          {evidence.page || "未标注"} · 位置：
                          {valueText(evidence.bbox)}
                        </div>
                        {joint && (
                          <Link
                            to={`/engineering/revisions/${data.release.product_revision_id}/review?joint=${joint.id}`}
                          >
                            在图纸中定位焊缝
                          </Link>
                        )}
                        <div>前置步骤：{prerequisites.join("、") || "无"}</div>
                        <div>
                          WPS：
                          {process.wps?.wps_number || task.wps_id || "不适用"} /
                          版本 {process.wps?.revision || "未记录"}；PQR：
                          {process.pqr?.pqr_number || task.pqr_id || "不适用"} /
                          快照时间 {process.pqr?.updated_at || "未记录"}
                        </div>
                        {process.segment && (
                          <div>
                            分段范围：{process.segment.start_mm}–
                            {process.segment.end_mm} mm
                          </div>
                        )}
                        {process.treatment && (
                          <div>
                            热处理：
                            {process.treatment.scope === "global"
                              ? "整体"
                              : "局部"}{" "}
                            · {process.treatment.temperature_min}–
                            {process.treatment.temperature_max} ℃ · 保温{" "}
                            {process.treatment.hold_minutes} min
                          </div>
                        )}
                        <div>
                          检验要求：{inspectionText(step.inspection_node)}
                        </div>
                      </div>
                      <div>
                        <QRCode type="svg" value={linkFor(task)} size={108} />
                        <a href={linkFor(task)}>扫码定位本工序</a>
                      </div>
                    </div>
                    <Table<Row>
                      size="small"
                      pagination={false}
                      rowKey="id"
                      dataSource={inspections}
                      columns={[
                        { title: "检验记录", dataIndex: "inspection_number" },
                        {
                          title: "结果",
                          dataIndex: "inspection_result",
                          render: (value) => labels[value] || value,
                        },
                        {
                          title: "返修与复验",
                          render: (_, item) =>
                            `${item.repair_required ? "需返修" : "无返修要求"} · ${item.reinspection_result || "未复验"} · ${item.reinspection_notes || ""}`,
                        },
                      ]}
                    />
                    <Table<Row>
                      size="small"
                      pagination={false}
                      rowKey="id"
                      dataSource={traces}
                      columns={[
                        { title: "执行时间", dataIndex: "recorded_at" },
                        { title: "焊工 ID", dataIndex: "welder_id" },
                        { title: "设备 ID", dataIndex: "equipment_id" },
                        { title: "登记人 ID", dataIndex: "recorded_by" },
                        {
                          title: "记录类型",
                          dataIndex: "status",
                          render: (value) => labels[value] || value,
                        },
                        {
                          title: "实际参数",
                          dataIndex: "actual_parameters",
                          render: parametersText,
                        },
                        {
                          title: "焊材事件",
                          dataIndex: "consumable_usage_event_ids",
                          render: valueText,
                        },
                      ]}
                    />
                    <Button
                      className="delivery-no-print"
                      onClick={() => {
                        setParams({
                          task: String(task.id),
                          ...(task.source_weld_joint_id
                            ? { joint: task.source_weld_joint_id }
                            : {}),
                        });
                        document
                          .getElementById("delivery-execution")
                          ?.scrollIntoView({ behavior: "smooth" });
                      }}
                    >
                      选择此步骤登记执行
                    </Button>
                  </Card>
                );
              })}
              <Card title="冻结领用材料与实际流水">
                <div>
                  领用单：
                  {data.issue?.document?.document_number ||
                    "未关联或旧批次无快照"}
                </div>
                <Table<Row>
                  size="small"
                  pagination={false}
                  rowKey="id"
                  dataSource={data.issue?.items || []}
                  columns={[
                    { title: "材料", dataIndex: "material_name" },
                    { title: "规格", dataIndex: "specification" },
                    { title: "批次要求", dataIndex: "batch_requirement" },
                    { title: "建议领用量", dataIndex: "suggested_quantity" },
                    { title: "单位", dataIndex: "unit" },
                  ]}
                />
                <Table<Row>
                  size="small"
                  pagination={false}
                  rowKey="id"
                  dataSource={data.usage_events || []}
                  columns={[
                    { title: "事件编号", dataIndex: "id" },
                    { title: "类型", dataIndex: "event_type" },
                    { title: "材料 ID", dataIndex: "material_id" },
                    { title: "材料批号", dataIndex: "batch_number" },
                    { title: "数量", dataIndex: "quantity" },
                    { title: "单位", dataIndex: "unit" },
                  ]}
                />
              </Card>
            </div>
            <div className="delivery-no-print" id="delivery-execution">
              <ProductionReleasePanel
                sequenceId={sequenceId}
                approved
                onRecordsChange={() => setReload((value) => value + 1)}
                taskIds={tasks.map((task) => task.id)}
              />
            </div>
          </>
        )}
      </div>
    </Spin>
  );
}
