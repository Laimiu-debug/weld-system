import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Table,
  message,
} from "antd";
import { v4 as uuid } from "uuid";
import {
  productionReleaseService as service,
  ReleaseDetail,
  ReleasedTask,
} from "@/services/productionRelease";
import weldersService from "@/services/welders";
import equipmentService from "@/services/equipment";
import SequenceChangePanel from "./SequenceChangePanel";
import { Link } from "react-router-dom";

function errorText(error: any): string {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message)
    return [detail.message, ...(detail.qualification?.reasons || [])].join(
      "；",
    );
  return error?.message || "操作失败，请重试";
}

export default function ProductionReleasePanel({
  sequenceId,
  approved,
  onSequenceChange,
}: {
  sequenceId: string;
  approved: boolean;
  onSequenceChange?: (id: string) => void;
}) {
  const [detail, setDetail] = useState<ReleaseDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [action, setAction] = useState<{
    type: "assign" | "complete";
    task: ReleasedTask;
  } | null>(null);
  const [welders, setWelders] = useState<{ value: number; label: string }[]>(
    [],
  );
  const [equipment, setEquipment] = useState<
    { value: number; label: string }[]
  >([]);
  const [resourceError, setResourceError] = useState("");
  const [issueLists, setIssueLists] = useState<
    { id: string; document_number: string }[]
  >([]);
  const [issueListId, setIssueListId] = useState<string>();
  const [pendingExecution, setPendingExecution] = useState(false);
  const [search, setSearch] = useState("");
  const [form] = Form.useForm();
  const generation = useRef(0);
  const draftKey = (task: number) =>
    `production-execution:${sequenceId}:${task}`;
  const load = useCallback(async () => {
    const request = ++generation.current;
    setLoading(true);
    try {
      const [result, lists] = await Promise.all([
        service.forSequence(sequenceId),
        service.issueLists(sequenceId),
      ]);
      if (request !== generation.current) return;
      setDetail(result);
      setIssueLists(lists);
      setError("");
    } catch (e) {
      if (request === generation.current) setError(errorText(e));
    } finally {
      if (request === generation.current) setLoading(false);
    }
  }, [sequenceId]);
  useEffect(() => {
    void load();
    return () => {
      generation.current += 1;
    };
  }, [load]);
  useEffect(() => {
    if (action?.type !== "assign") return;
    let active = true;
    const timer = window.setTimeout(async () => {
      try {
        const [w, e] = await Promise.all([
          weldersService.getList({ limit: 50, search }),
          equipmentService.getEquipmentList({ limit: 50, search }),
        ]);
        if (!active) return;
        setWelders(
          w.data.items.map((item) => ({
            value: Number(item.id),
            label: item.full_name || item.welder_code,
          })),
        );
        setEquipment(
          e.items.map((item) => ({
            value: Number(item.id),
            label: item.equipment_name,
          })),
        );
        setResourceError("");
      } catch (e) {
        if (active) setResourceError(errorText(e));
      }
    }, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [action?.type, search]);
  const open = (type: "assign" | "complete", task: ReleasedTask) => {
    form.resetFields();
    setSearch("");
    setResourceError("");
    if (type === "assign")
      form.setFieldsValue({
        welder_id: task.assigned_welder_id,
        equipment_id: task.assigned_equipment_id ?? undefined,
      });
    setPendingExecution(false);
    if (type === "complete") {
      const saved = sessionStorage.getItem(draftKey(task.id));
      const draft = saved ? JSON.parse(saved) : null;
      setPendingExecution(!!draft);
      form.setFieldsValue(
        draft
          ? {
              ...draft.parameters,
              usage_ids: draft.events,
              execution_status: draft.status,
            }
          : { execution_status: "completed" },
      );
    }
    setAction({ type, task });
  };
  const submit = async () => {
    if (!action) return;
    let values: Record<string, any>;
    try {
      values = await form.validateFields();
    } catch {
      return;
    }
    setBusy(true);
    try {
      let pendingOverride = false;
      if (action.type === "assign") {
        const result = await service.assign(action.task.id, {
          welder_id: values.welder_id,
          equipment_id: values.equipment_id ?? undefined,
          override_reason: values.override_reason?.trim() || undefined,
        });
        pendingOverride = result.qualification_status === "pending_override";
      } else {
        const parameters = Object.fromEntries(
          Object.entries(values).filter(
            ([, value]) => typeof value === "number",
          ),
        ) as Record<string, number>;
        const key = draftKey(action.task.id);
        const saved = sessionStorage.getItem(key);
        const draft = saved
          ? JSON.parse(saved)
          : {
              key: uuid(),
              parameters,
              events: values.usage_ids || [],
              status: values.execution_status || "completed",
            };
        sessionStorage.setItem(key, JSON.stringify(draft));
        setPendingExecution(true);
        await service.complete(
          action.task.id,
          draft.key,
          draft.parameters,
          draft.events,
          draft.status,
        );
        sessionStorage.removeItem(key);
        setPendingExecution(false);
      }
      message.success(
        pendingOverride
          ? "特批申请已提交，批准后才会分配资源"
          : action.type === "assign"
            ? "派工成功"
            : "执行记录已保存",
      );
      setAction(null);
      await load();
    } catch (e) {
      const status = (e as any)?.response?.status;
      if (
        action.type === "complete" &&
        status >= 400 &&
        status < 500 &&
        status !== 408
      ) {
        sessionStorage.removeItem(draftKey(action.task.id));
        setPendingExecution(false);
      }
      message.error(errorText(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Card
      title="生产放行与执行"
      extra={
        <Button disabled={busy} loading={loading} onClick={() => void load()}>
          刷新任务
        </Button>
      }
    >
      {error ? (
        <Alert type="error" showIcon message={error} />
      ) : !detail ? (
        <Space direction="vertical">
          <span>将当前批准焊序转为生产任务，后续按工序依赖执行。</span>
          <Select
            aria-label="关联焊材领用单"
            placeholder="关联已批准的领用单（可选）"
            allowClear
            style={{ minWidth: 300 }}
            value={issueListId}
            onChange={setIssueListId}
            options={issueLists.map((item) => ({
              value: item.id,
              label: item.document_number,
            }))}
          />
          <Button
            type="primary"
            disabled={!approved || loading}
            loading={busy}
            onClick={() =>
              Modal.confirm({
                title: "确认下发当前焊序？",
                content: "将创建对应的生产任务和质量检验节点。",
                onOk: async () => {
                  setBusy(true);
                  try {
                    await service.release(sequenceId, issueListId);
                    message.success("生产任务已下发");
                    await load();
                  } catch (e) {
                    message.error(errorText(e));
                    throw e;
                  } finally {
                    setBusy(false);
                  }
                },
              })
            }
          >
            下发生产
          </Button>
        </Space>
      ) : (
        <Table<ReleasedTask>
          rowKey="id"
          loading={loading}
          scroll={{ x: 700 }}
          dataSource={[...detail.tasks].sort(
            (a, b) =>
              (a.source_step_snapshot?.order_index || 0) -
              (b.source_step_snapshot?.order_index || 0),
          )}
          columns={[
            { title: "工序", dataIndex: "task_name" },
            {
              title: "状态",
              dataIndex: "status",
              render: (value: string) =>
                ({
                  pending: "待执行",
                  in_progress: "执行中",
                  completed: "已完成",
                  cancelled: "已取消",
                })[value] || value,
            },
            {
              title: "派工",
              render: (_, task) =>
                task.assigned_welder_id ? "已分配焊工" : "未分配",
            },
            {
              title: "操作",
              render: (_, task) => (
                <Space>
                  {task.task_type === "welding" && (
                    <Button
                      disabled={
                        busy ||
                        ["completed", "cancelled"].includes(task.status) ||
                        detail.release.status !== "released"
                      }
                      onClick={() => open("assign", task)}
                    >
                      派工
                    </Button>
                  )}
                  <Button
                    disabled={
                      busy ||
                      ["completed", "cancelled"].includes(task.status) ||
                      detail.release.status !== "released"
                    }
                    onClick={() => open("complete", task)}
                  >
                    登记执行
                  </Button>
                  {(detail.quality_nodes || [])
                    .filter((node) => node.production_task_id === task.id)
                    .map((node) => (
                      <Link
                        key={node.id}
                        to={`/quality/${node.quality_inspection_id}/edit`}
                      >
                        填写检验
                      </Link>
                    ))}
                </Space>
              ),
            },
          ]}
        />
      )}
      {detail && (
        <>
          <Alert
            type={detail.release.status === "released" ? "info" : "warning"}
            message={
              detail.release.status === "released"
                ? `当前批次可执行；${detail.release.consumable_issue_list_id ? "已关联焊材领用单" : "未关联领用单"}`
                : "原批次已停止执行，历史记录保留"
            }
          />
          <SequenceChangePanel
            detail={detail}
            reload={load}
            select={onSequenceChange}
          />
          <Card size="small" title="执行历史">
            <Table
              rowKey="id"
              dataSource={detail.executions || []}
              columns={[
                {
                  title: "工序",
                  render: (_, item) =>
                    detail.tasks.find(
                      (task) => task.id === item.production_task_id,
                    )?.task_name,
                },
                {
                  title: "状态",
                  render: (_, item) =>
                    item.status === "completed" ? "已完工" : "过程记录",
                },
                {
                  title: "实际参数",
                  render: (_, item) =>
                    Object.entries(item.actual_parameters)
                      .map(
                        ([key, value]) =>
                          `${({ current: "电流(A)", voltage: "电压(V)", travel_speed: "焊速(mm/min)", heat_input: "热输入(kJ/mm)", preheat_temperature: "预热(℃)", interpass_temperature: "层间温度(℃)" } as Record<string, string>)[key] || key}: ${value}`,
                      )
                      .join("；"),
                },
                {
                  title: "关联焊材记录",
                  render: (_, item) => item.consumable_usage_event_ids.length,
                },
                { title: "记录时间", dataIndex: "recorded_at" },
              ]}
            />
          </Card>
        </>
      )}
      {!!detail?.authorizations?.length && (
        <Card size="small" title="资格特批记录">
          <Table
            rowKey="id"
            dataSource={detail.authorizations.filter(
              (item) => item.override_reason,
            )}
            columns={[
              {
                title: "工序",
                render: (_, item) =>
                  detail.tasks.find(
                    (task) => task.id === item.production_task_id,
                  )?.task_name || "关联工序",
              },
              { title: "申请理由", dataIndex: "override_reason" },
              {
                title: "资格问题",
                render: (_, item) =>
                  item.qualification_snapshot?.reasons?.join("；"),
              },
              {
                title: "状态",
                dataIndex: "qualification_status",
                render: (status: string) =>
                  ({
                    pending_override: "待特批",
                    authorized: "已批准",
                    rejected: "已拒绝",
                    qualified: "资格满足",
                  })[status] || status,
              },
              {
                title: "操作",
                render: (_, item) =>
                  item.qualification_status === "pending_override" && (
                    <Space>
                      {[true, false].map((approve) => (
                        <Button
                          key={String(approve)}
                          disabled={busy}
                          danger={!approve}
                          onClick={() =>
                            Modal.confirm({
                              title: approve
                                ? "批准这项资格例外？"
                                : "拒绝这项资格例外？",
                              content: item.override_reason,
                              onOk: async () => {
                                setBusy(true);
                                try {
                                  await service.decide(item.id, approve);
                                  message.success("处理结果已保存");
                                  await load();
                                } catch (e) {
                                  message.error(errorText(e));
                                  throw e;
                                } finally {
                                  setBusy(false);
                                }
                              },
                            })
                          }
                        >
                          {approve ? "批准" : "拒绝"}
                        </Button>
                      ))}
                    </Space>
                  ),
              },
            ]}
          />
        </Card>
      )}
      <Modal
        open={!!action}
        title={`${action?.type === "assign" ? "分配资源" : "登记执行"}：${action?.task.task_name || ""}`}
        confirmLoading={busy}
        onOk={() => void submit()}
        onCancel={() => !busy && setAction(null)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" preserve={false}>
          {action?.type === "assign" ? (
            <>
              <Input.Search
                placeholder="按名称搜索焊工和设备（显示前 50 项）"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              {resourceError && <Alert type="error" message={resourceError} />}
              <Form.Item
                name="welder_id"
                label="焊工"
                rules={[{ required: true, message: "请选择焊工" }]}
              >
                <Select showSearch optionFilterProp="label" options={welders} />
              </Form.Item>
              <Form.Item name="equipment_id" label="设备（可选）">
                <Select
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  options={equipment}
                />
              </Form.Item>
              <Form.Item
                name="override_reason"
                label="资格例外理由（可选）"
                extra="资格不满足时，填写理由将提交特批申请，批准前不会分配资源。"
                rules={[
                  {
                    validator: (_, value) =>
                      !value ||
                      (value.trim().length >= 5 && value.trim().length <= 1000)
                        ? Promise.resolve()
                        : Promise.reject(new Error("请填写 5～1000 字的理由")),
                  },
                ]}
              >
                <Input.TextArea rows={3} maxLength={1000} />
              </Form.Item>
            </>
          ) : (
            <>
              {pendingExecution && (
                <Alert
                  type="warning"
                  message="上次请求结果未确认，再次提交会复用原请求。可刷新查看执行历史；确认前保留原输入。"
                />
              )}
              <Form.Item
                name="execution_status"
                label="记录类型"
                rules={[{ required: true }]}
              >
                <Select
                  disabled={pendingExecution}
                  options={[
                    { value: "recorded", label: "保存过程记录" },
                    { value: "completed", label: "确认完工" },
                  ]}
                />
              </Form.Item>
              <Alert
                type="info"
                message="请确认工序实际完成。前置工序、检验结果和资源资格由系统检查；检查不通过时不会保存完工。"
              />
              {action?.task.task_type === "welding" && (
                <>
                  <Form.Item name="current" label="实际电流（A）">
                    <InputNumber min={0} disabled={pendingExecution} />
                  </Form.Item>
                  <Form.Item name="voltage" label="实际电压（V）">
                    <InputNumber min={0} disabled={pendingExecution} />
                  </Form.Item>
                  {(
                    [
                      ["travel_speed", "焊速（mm/min）"],
                      ["heat_input", "热输入（kJ/mm）"],
                      ["preheat_temperature", "预热温度（℃）"],
                      ["interpass_temperature", "层间温度（℃）"],
                    ] as const
                  ).map(([name, label]) => (
                    <Form.Item key={name} name={name} label={label}>
                      <InputNumber
                        disabled={pendingExecution}
                        min={name.includes("temperature") ? undefined : 0}
                      />
                    </Form.Item>
                  ))}
                  <Form.Item name="usage_ids" label="关联实际焊材记录">
                    <Select
                      mode="multiple"
                      disabled={pendingExecution}
                      options={(detail?.usage_events || []).map((event) => ({
                        value: event.id,
                        label: `${event.event_type} ${event.quantity} ${event.unit} · ${event.id.slice(0, 8)}`,
                      }))}
                    />
                  </Form.Item>
                </>
              )}
            </>
          )}
        </Form>
      </Modal>
    </Card>
  );
}
