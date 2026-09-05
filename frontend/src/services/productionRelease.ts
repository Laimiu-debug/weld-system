import api from "./api";

export interface ReleasedTask {
  id: number;
  task_number: string;
  task_name: string;
  task_type: string;
  status: string;
  assigned_welder_id: number | null;
  assigned_equipment_id: number | null;
  source_step_snapshot: {
    order_index?: number;
    process_parameters?: { wps?: Record<string, unknown> };
  };
}
export interface ReleaseDetail {
  source_impact?: import("@/pages/Engineering/SourceImpactAlert").SourceImpact;
  release: { id: string; status: string; consumable_issue_list_id?: string };
  tasks: ReleasedTask[];
  authorizations: ResourceAuthorization[];
  change_requests: SequenceChange[];
  executions: {
    id: string;
    production_task_id: number;
    status: string;
    actual_parameters: Record<string, number>;
    recorded_at: string;
    consumable_usage_event_ids: string[];
  }[];
  quality_nodes: {
    id: string;
    production_task_id: number;
    quality_inspection_id: number;
  }[];
  usage_events: {
    id: string;
    event_type: string;
    quantity: number;
    unit: string;
  }[];
}
export interface SequenceChange {
  id: string;
  status: string;
  reason: string;
  source_sequence_revision_id: string;
  proposed_sequence_revision_id?: string;
  approval_instance_id?: number;
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
  async delivery(sequenceId: string): Promise<Record<string, any>> {
    return (
      await api.get(`/production-release/sequences/${sequenceId}/delivery`)
    ).data;
  },
  async forSequence(id: string): Promise<ReleaseDetail | null> {
    return (await api.get(`${root}/sequences/${id}/release`)).data;
  },
  async issueLists(
    id: string,
  ): Promise<{ id: string; document_number: string }[]> {
    return (await api.get(`${root}/sequences/${id}/issue-lists`)).data;
  },
  async requestChange(
    id: string,
    reason: string,
    workflow_id?: number,
  ): Promise<SequenceChange> {
    return (
      await api.post(`${root}/releases/${id}/change-requests`, {
        reason,
        workflow_id,
      })
    ).data;
  },
  async applyChange(id: string, proposed_sequence_revision_id: string) {
    return (
      await api.post(`${root}/change-requests/${id}/apply`, {
        proposed_sequence_revision_id,
      })
    ).data;
  },
  async release(id: string, consumable_issue_list_id?: string) {
    return (
      await api.post(`${root}/sequences/${id}/release`, {
        consumable_issue_list_id,
      })
    ).data;
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
    consumable_usage_event_ids: string[] = [],
    status: "recorded" | "completed" = "completed",
  ) {
    return (
      await api.post(`${root}/tasks/${id}/execution`, {
        idempotency_key: key,
        status,
        actual_parameters,
        consumable_usage_event_ids,
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
