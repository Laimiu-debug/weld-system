import React, { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Input,
  InputNumber,
  Modal,
  Space,
  Table,
  message,
} from "antd";
import {
  productionReleaseService as service,
  ReleaseDetail,
} from "@/services/productionRelease";
import { sequenceService, SequenceRow } from "@/services/sequence";

export const productionError = (error: any): string => {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string"
    ? detail
    : detail?.message || error?.message || "操作失败，请重试";
};

export default function SequenceChangePanel({
  detail,
  reload,
  select,
}: {
  detail: ReleaseDetail;
  reload: () => Promise<void>;
  select?: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [proposals, setProposals] = useState<Record<string, SequenceRow>>({});
  const [form] = Form.useForm();
  const [strategyForm] = Form.useForm();
  const [recalculating, setRecalculating] = useState<{
    id: string;
    source: string;
    reason: string;
    structure: Record<string, unknown>;
  } | null>(null);
  useEffect(() => {
    let active = true;
    const ids = (detail.change_requests || [])
      .map((r) => r.proposed_sequence_revision_id)
      .filter(Boolean) as string[];
    Promise.all(
      ids.map(
        async (id) =>
          [id, (await sequenceService.detail(id)).revision] as const,
      ),
    )
      .then((rows) => {
        if (active) {
          setProposals(Object.fromEntries(rows));
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(productionError(e));
      });
    return () => {
      active = false;
    };
  }, [detail]);
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      await reload();
    } catch (e) {
      setError(productionError(e));
      message.error(productionError(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Card
      size="small"
      title="已放行焊序变更"
      extra={
        <Button
          disabled={
            busy ||
            detail.release.status !== "released" ||
            (detail.change_requests || []).some((r) =>
              ["pending", "approved"].includes(r.status),
            )
          }
          onClick={() => {
            form.resetFields();
            setOpen(true);
          }}
        >
          申请变更
        </Button>
      }
    >
      <Alert
        type="info"
        message="申请批准 → 重算方案 → 核对并批准新焊序 → 应用变更 → 在新版本下发生产。应用后原批次停止执行，历史记录保留；新批次不会自动继承完工记录。"
      />
      {error && <Alert type="error" message={error} />}
      <Table
        rowKey="id"
        dataSource={detail.change_requests || []}
        columns={[
          { title: "变更理由", dataIndex: "reason" },
          {
            title: "状态",
            render: (_, row) =>
              ({
                pending: "待审批",
                approved: "已批准",
                rejected: "已拒绝",
                applied: "已应用",
              })[row.status] || row.status,
          },
          {
            title: "审批实例",
            render: (_, row) =>
              row.approval_instance_id || "按当前工作区规则处理",
          },
          {
            title: "操作",
            render: (_, row) => (
              <Space wrap>
                {row.status === "approved" && (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        const source = (
                          await sequenceService.detail(
                            row.source_sequence_revision_id,
                          )
                        ).revision;
                        const policy = source.strategy_snapshot || {};
                        strategyForm.setFieldsValue({
                          symmetric: policy.symmetric ?? true,
                          segmented: policy.segmented ?? false,
                          skip_weld: policy.skip_weld ?? false,
                          segment_length_mm:
                            policy._structure?.segment_length_mm || 500,
                        });
                        setRecalculating({
                          id: row.id,
                          source: row.source_sequence_revision_id,
                          reason: row.reason,
                          structure: policy._structure || {},
                        });
                      })
                    }
                  >
                    {row.proposed_sequence_revision_id
                      ? "重新生成方案"
                      : "重算方案"}
                  </Button>
                )}
                {row.proposed_sequence_revision_id && (
                  <Button
                    disabled={busy}
                    onClick={() => select?.(row.proposed_sequence_revision_id!)}
                  >
                    查看新焊序
                  </Button>
                )}
                {row.status === "approved" &&
                  row.proposed_sequence_revision_id && (
                    <>
                      {["draft", "returned", "rejected"].includes(
                        proposals[row.proposed_sequence_revision_id]?.status,
                      ) && (
                        <Button
                          disabled={busy}
                          onClick={() =>
                            void run(async () => {
                              const result = await sequenceService.submit(
                                row.proposed_sequence_revision_id!,
                              );
                              message.success(
                                result.status === "approved"
                                  ? "新焊序已批准冻结"
                                  : "新焊序已提交审批",
                              );
                            })
                          }
                        >
                          提交新焊序审批
                        </Button>
                      )}
                      <Button
                        disabled={
                          busy ||
                          proposals[row.proposed_sequence_revision_id]
                            ?.status !== "approved"
                        }
                        onClick={() =>
                          Modal.confirm({
                            title: "应用已批准的新焊序？",
                            content:
                              "原批次将停止执行，原任务状态和历史记录保留。随后请在新版本重新下发。",
                            onOk: async () => {
                              setBusy(true);
                              try {
                                await service.applyChange(
                                  row.id,
                                  row.proposed_sequence_revision_id!,
                                );
                                await reload();
                                message.success("变更已应用");
                              } catch (e) {
                                message.error(productionError(e));
                                throw e;
                              } finally {
                                setBusy(false);
                              }
                            },
                          })
                        }
                      >
                        应用变更
                      </Button>
                    </>
                  )}
              </Space>
            ),
          },
        ]}
      />
      <Modal
        open={open}
        title="申请生产焊序变更"
        confirmLoading={busy}
        onCancel={() => !busy && setOpen(false)}
        onOk={async () => {
          let values;
          try {
            values = await form.validateFields();
          } catch {
            return;
          }
          await run(async () => {
            await service.requestChange(
              detail.release.id,
              values.reason.trim(),
              values.workflow_id,
            );
            setOpen(false);
            message.success("变更申请已保存");
          });
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="reason"
            label="变更原因及影响"
            rules={[{ required: true, min: 5, max: 2000, whitespace: true }]}
          >
            <Input.TextArea rows={4} maxLength={2000} />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        open={!!recalculating}
        title="重算变更方案"
        confirmLoading={busy}
        onCancel={() => !busy && setRecalculating(null)}
        onOk={async () => {
          if (!recalculating) return;
          let values;
          try {
            values = await strategyForm.validateFields();
          } catch {
            return;
          }
          await run(async () => {
            await sequenceService.recalculate(recalculating.source, {
              change_request_id: recalculating.id,
              change_summary: recalculating.reason,
              strategies: {
                symmetric: values.symmetric,
                segmented: values.segmented,
                skip_weld: values.skip_weld,
                closed_space_first: true,
              },
              structure: {
                ...recalculating.structure,
                segment_length_mm: values.segment_length_mm,
              },
            });
            setRecalculating(null);
            message.success("变更方案已生成，请核对后提交审批");
          });
        }}
      >
        <Form form={strategyForm} layout="vertical">
          <Form.Item name="symmetric" valuePropName="checked">
            <Checkbox>同类焊缝两端交错排序</Checkbox>
          </Form.Item>
          <Form.Item name="segmented" valuePropName="checked">
            <Checkbox>分段焊接</Checkbox>
          </Form.Item>
          <Form.Item name="skip_weld" valuePropName="checked">
            <Checkbox>跳焊（先奇数段再偶数段）</Checkbox>
          </Form.Item>
          <Form.Item
            name="segment_length_mm"
            label="每段最大长度（mm）"
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={100000} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
