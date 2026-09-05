import { beforeEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import SequenceDelivery from "../src/pages/Engineering/SequenceDelivery";
import { productionReleaseService as service } from "../src/services/productionRelease";

vi.mock("../src/services/productionRelease", () => ({
  productionReleaseService: { delivery: vi.fn() },
}));
vi.mock("../src/pages/Engineering/ProductionReleasePanel", () => ({
  default: ({ taskIds }: { taskIds: number[] }) => (
    <div data-testid="execution">{taskIds.join(",")}</div>
  ),
}));

const task = (id: number, joint: string) => ({
  id,
  task_name: `工序 ${id}`,
  status: "pending",
  source_weld_joint_id: joint,
  source_step_snapshot: {
    step_code: `WELD-${id}`,
    order_index: id,
    process_parameters: {
      wps: { wps_number: "WPS-001", revision: "A" },
      pqr: { pqr_number: "PQR-001", updated_at: "2026-09-05" },
    },
  },
});
const packageData = () => ({
  release: {
    id: "batch",
    product_revision_id: "rev",
    sequence_frozen_hash: "frozen",
  },
  drawing: {
    filename: '<script>alert("x")</script>.pdf',
    weld_joints: [
      {
        id: "joint1",
        weld_number: "W1",
        evidence: { page: 2, bbox: [1, 2, 3, 4] },
      },
      { id: "joint2", weld_number: "W2" },
    ],
  },
  frozen_sequence: {
    dependencies: [{ predecessor_code: "ASM", successor_code: "WELD-1" }],
  },
  tasks: [task(1, "joint1"), task(2, "joint2")],
  inspections: [
    {
      id: 1,
      production_task_id: 1,
      inspection_number: "RT-001",
      inspection_result: "pass",
    },
  ],
  executions: [
    {
      id: "trace1",
      production_task_id: 1,
      actual_parameters: { current: 100 },
      status: "completed",
    },
  ],
  source_impact: {
    stale: true,
    affected_joint_ids: ["joint1"],
    notice: "保留历史快照",
    issues: [
      {
        source_type: "wps",
        source_id: 1,
        joint_ids: ["joint1"],
        message: "WPS 已更新",
      },
    ],
  },
});
function mount(query = "") {
  return render(
    <MemoryRouter
      initialEntries={[`/engineering/sequences/seq/delivery${query}`]}
    >
      <Routes>
        <Route
          path="/engineering/sequences/:sequenceId/delivery"
          element={<SequenceDelivery />}
        />
      </Routes>
    </MemoryRouter>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(service.delivery).mockResolvedValue(packageData() as any);
});

it("links frozen drawing positions, source impacts and records to a QR task without executing it", async () => {
  mount("?task=1&joint=joint1");
  await screen.findByText("1. 工序 1");
  expect(screen.queryByText("2. 工序 2")).toBeNull();
  expect(screen.getByTestId("execution").textContent).toBe("1");
  expect(screen.getByText("在图纸中定位焊缝").getAttribute("href")).toContain(
    "/rev/review?joint=joint1",
  );
  expect(screen.getByText("扫码定位本工序").getAttribute("href")).toContain(
    "/seq/delivery?task=1&joint=joint1",
  );
  expect(document.querySelector(".ant-qrcode svg")).not.toBeNull();
  expect(screen.getByText(/WPS 已更新/)).toBeTruthy();
  expect(screen.getByText("RT-001")).toBeTruthy();
  fireEvent.click(screen.getByText("查看该焊缝全部工序"));
  expect(screen.getByTestId("execution").textContent).toBe("1");
  expect(service.delivery).toHaveBeenCalledTimes(1);
});

it("exports escaped HTML with embedded QR and absolute drawing links", async () => {
  const blobs: Blob[] = [];
  URL.createObjectURL = vi.fn((blob: Blob) => {
    blobs.push(blob);
    return "blob:qa";
  });
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  mount("?task=1");
  await screen.findByText("1. 工序 1");
  fireEvent.click(screen.getByText("导出可打印 HTML"));
  await waitFor(() => expect(blobs).toHaveLength(1));
  const html = await new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.readAsText(blobs[0]);
  });
  expect(html).toContain("&lt;script&gt;");
  expect(html).not.toContain('<script>alert("x")');
  expect(html).toContain("<svg");
  expect(html).toContain(
    `${window.location.origin}/engineering/revisions/rev/review?joint=joint1`,
  );
  expect(html).not.toContain("选择此步骤登记执行");
  expect(html).not.toContain("2. 工序 2");
});

it("denies export and execution when the package cannot be accessed", async () => {
  vi.mocked(service.delivery).mockRejectedValue(new Error("Forbidden"));
  mount();
  await screen.findByText(/交付包加载失败/);
  expect(
    (screen.getByRole("button", { name: "导出完整数据" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  expect(screen.queryByTestId("execution")).toBeNull();
});
