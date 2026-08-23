import api from "./api";

export type MatchRow = Record<string, any>;
export interface MatchDetail {
  run: MatchRow;
  candidates: MatchRow[];
  gaps: MatchRow[];
  freezes: MatchRow[];
}

export const matchingService = {
  async runs(revisionId: string): Promise<MatchRow[]> {
    return (await api.get(`/matching/revisions/${revisionId}/runs`)).data;
  },
  async run(revisionId: string, data: MatchRow = {}): Promise<MatchRow> {
    return (await api.post(`/matching/revisions/${revisionId}/runs`, data))
      .data;
  },
  async detail(runId: string): Promise<MatchDetail> {
    return (await api.get(`/matching/runs/${runId}`)).data;
  },
  async confirm(
    candidateId: string,
    status: "confirmed" | "rejected",
    note?: string,
  ): Promise<MatchRow> {
    return (
      await api.post(`/matching/candidates/${candidateId}/confirm`, {
        status,
        note,
      })
    ).data;
  },
  async approve(runId: string, note?: string): Promise<MatchRow> {
    return (await api.post(`/matching/runs/${runId}/approve`, { note })).data;
  },
  async linkGap(gapId: string, data: MatchRow): Promise<MatchRow> {
    return (await api.post(`/matching/gaps/${gapId}/link`, data)).data;
  },
};
