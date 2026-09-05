import api from "./api";

export interface ReleasedTask {
  id: number;
  task_number: string;
  task_name: string;
  task_type: string;
  status: string;
  assigned_welder_id: number | null;
  assigned_equipment_id: number | null;
  source_step_snapshot: { order_index?: number };
}
export interface ReleaseDetail {
  release: { id: string; status: string };
  tasks: ReleasedTask[];
  authorizations: ResourceAuthorization[];
}
export interface ResourceAuthorization {
  id: string;
  production_task_id: number;
  qualification_status: string;
  override_reason: string | null;
  qualification_snapshot: { reasons?: string[] };
}
const root = "/production-release";
export const productionReleaseService = {
  async forSequence(id: string): Promise<ReleaseDetail | null> {
    return (await api.get(`${root}/sequences/${id}/release`)).data;
  },
  async release(id: string) {
    return (await api.post(`${root}/sequences/${id}/release`, {})).data;
  },
  async assign(
    id: number,
    data: {
      welder_id: number;
      equipment_id?: number;
      override_reason?: string;
    },
  ) {
    return (await api.post(`${root}/tasks/${id}/assign`, data)).data;
  },
  async complete(
    id: number,
    key: string,
    actual_parameters: Record<string, number>,
  ) {
    return (
      await api.post(`${root}/tasks/${id}/execution`, {
        idempotency_key: key,
        status: "completed",
        actual_parameters,
      })
    ).data;
  },
  async decide(id: string, approve: boolean) {
    return (
      await api.post(`${root}/resource-authorizations/${id}/decision`, {
        approve,
      })
    ).data;
  },
};
