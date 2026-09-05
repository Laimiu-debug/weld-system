import { beforeEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { message } from "antd";
import ProductionReleasePanel from "../src/pages/Engineering/ProductionReleasePanel";
import {
  productionReleaseService as service,
  ReleaseDetail,
} from "../src/services/productionRelease";
import { sequenceService } from "../src/services/sequence";

vi.mock("../src/services/productionRelease", () => ({
  productionReleaseService: {
    forSequence: vi.fn(),
    issueLists: vi.fn(),
    release: vi.fn(),
    complete: vi.fn(),
    requestChange: vi.fn(),
    applyChange: vi.fn(),
    assign: vi.fn(),
    decide: vi.fn(),
  },
}));
vi.mock("../src/services/sequence", () => ({
  sequenceService: { detail: vi.fn(), recalculate: vi.fn(), submit: vi.fn() },
}));
vi.mock("../src/services/welders", () => ({ default: { getList: vi.fn() } }));
vi.mock("../src/services/equipment", () => ({
  default: { getEquipmentList: vi.fn() },
}));

let detail: ReleaseDetail;
beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  detail = {
    release: { id: "release", status: "released" },
    tasks: [
      {
        id: 1,
        task_number: "T1",
        task_name: "组对检查",
        task_type: "assembly",
        status: "pending",
        assigned_welder_id: null,
        assigned_equipment_id: null,
        source_step_snapshot: { order_index: 1 },
      },
    ],
    authorizations: [],
    change_requests: [],
    executions: [],
    quality_nodes: [],
    usage_events: [],
  };
  vi.mocked(service.forSequence).mockImplementation(async () => detail);
  vi.mocked(service.issueLists).mockResolvedValue([]);
  vi.mocked(sequenceService.detail).mockResolvedValue({
    revision: { id: "new", status: "draft" },
    steps: [],
    dependencies: [],
  });
});
const show = () =>
  render(
    <MemoryRouter>
      <ProductionReleasePanel sequenceId="seq" approved />
    </MemoryRouter>,
  );

it("replays the same uncertain execution request after remount without duplicate success", async () => {
  const success = vi.spyOn(message, "success");
  vi.mocked(service.complete).mockRejectedValueOnce(new Error("网络中断"));
  const view = show();
  fireEvent.click(await screen.findByText("登记执行"));
  fireEvent.click(await screen.findByRole("button", { name: "OK" }));
  await waitFor(() => expect(service.complete).toHaveBeenCalledTimes(1));
  const first = vi.mocked(service.complete).mock.calls[0];
  await screen.findByText(/上次请求结果未确认/);
  expect(success).not.toHaveBeenCalled();
  view.unmount();
  vi.mocked(service.complete).mockResolvedValueOnce({ created: false });
  show();
  fireEvent.click(await screen.findByText("登记执行"));
  await screen.findByText(/上次请求结果未确认/);
  fireEvent.click(await screen.findByRole("button", { name: "OK" }));
  await waitFor(() => expect(service.complete).toHaveBeenCalledTimes(2));
  expect(vi.mocked(service.complete).mock.calls[1]).toEqual(first);
  await waitFor(() =>
    expect(sessionStorage.getItem("production-execution:seq:1")).toBeNull(),
  );
});

it("binds recalculation to the approved change and does not apply a draft", async () => {
  detail.change_requests = [
    {
      id: "change",
      status: "approved",
      reason: "调整分段策略",
      source_sequence_revision_id: "seq",
    },
  ];
  vi.mocked(sequenceService.recalculate).mockRejectedValueOnce(
    new Error("产品资料已变化"),
  );
  show();
  fireEvent.click(await screen.findByText("重算方案"));
  fireEvent.click(await screen.findByRole("button", { name: "OK" }));
  await waitFor(() =>
    expect(sequenceService.recalculate).toHaveBeenCalledWith(
      "seq",
      expect.objectContaining({
        change_request_id: "change",
        change_summary: "调整分段策略",
      }),
    ),
  );
  expect(service.applyChange).not.toHaveBeenCalled();
  await screen.findAllByText("产品资料已变化");
});

it("does not allow applying a proposal before it is approved", async () => {
  detail.change_requests = [
    {
      id: "change",
      status: "approved",
      reason: "调整分段策略",
      source_sequence_revision_id: "seq",
      proposed_sequence_revision_id: "new",
    },
  ];
  show();
  const apply = await screen.findByRole("button", { name: "应用变更" });
  expect((apply as HTMLButtonElement).disabled).toBe(true);
  expect(service.applyChange).not.toHaveBeenCalled();
});

it("keeps pending changes waiting for approval and displays history and quality links", async () => {
  detail.change_requests = [
    {
      id: "change",
      status: "pending",
      reason: "调整分段策略",
      source_sequence_revision_id: "seq",
      approval_instance_id: 42,
    },
  ];
  detail.quality_nodes = [
    { id: "node", production_task_id: 1, quality_inspection_id: 7 },
  ];
  detail.executions = [
    {
      id: "trace",
      production_task_id: 1,
      status: "recorded",
      actual_parameters: { current: 100 },
      recorded_at: "2026-09-05",
      consumable_usage_event_ids: [],
    },
  ];
  show();
  await screen.findByText("待审批");
  expect(screen.queryByText("重算方案")).toBeNull();
  expect(
    screen.getByRole("link", { name: "填写检验" }).getAttribute("href"),
  ).toBe("/quality/7/edit");
  expect(screen.getByText("电流(A): 100")).toBeTruthy();
  expect(sequenceService.recalculate).not.toHaveBeenCalled();
});

it("submits the selected approved issue list when releasing", async () => {
  vi.mocked(service.forSequence).mockResolvedValue(null);
  vi.mocked(service.issueLists).mockResolvedValue([
    { id: "issue", document_number: "领用单001" },
  ]);
  vi.mocked(service.release).mockResolvedValue({ created: true });
  show();
  const select = await screen.findByRole("combobox", {
    name: "关联焊材领用单",
  });
  fireEvent.mouseDown(select);
  fireEvent.click(await screen.findByText("领用单001"));
  fireEvent.click(screen.getByText("下发生产"));
  fireEvent.click(await screen.findByRole("button", { name: "OK" }));
  await waitFor(() =>
    expect(service.release).toHaveBeenCalledWith("seq", "issue"),
  );
});
