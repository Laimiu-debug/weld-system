import api from "./api";

export type SequenceRow = Record<string, any>;
export interface SequenceDetail {
  revision: SequenceRow;
  steps: SequenceRow[];
  dependencies: SequenceRow[];
}

export const sequenceService = {
  async list(productRevisionId: string): Promise<SequenceRow[]> {
    return (await api.get(`/sequences/product-revisions/${productRevisionId}`))
      .data;
  },
  async generate(
    productRevisionId: string,
    data: SequenceRow,
  ): Promise<SequenceRow> {
    return (
      await api.post(
        `/sequences/product-revisions/${productRevisionId}/generate`,
        data,
      )
    ).data;
  },
  async detail(sequenceId: string): Promise<SequenceDetail> {
    return (await api.get(`/sequences/revisions/${sequenceId}`)).data;
  },
  async reorder(sequenceId: string, data: SequenceRow): Promise<SequenceRow> {
    return (await api.post(`/sequences/revisions/${sequenceId}/reorder`, data))
      .data;
  },
  async recalculate(
    sequenceId: string,
    data: SequenceRow = {},
  ): Promise<SequenceRow> {
    return (
      await api.post(`/sequences/revisions/${sequenceId}/recalculate`, data)
    ).data;
  },
  async compare(leftId: string, rightId: string): Promise<SequenceRow> {
    return (
      await api.get("/sequences/comparisons", {
        params: { left_id: leftId, right_id: rightId },
      })
    ).data;
  },
  async submit(
    sequenceId: string,
    data: SequenceRow = {},
  ): Promise<SequenceRow> {
    return (await api.post(`/sequences/revisions/${sequenceId}/submit`, data))
      .data;
  },
  async productionRelease(productRevisionId: string): Promise<SequenceRow> {
    return (
      await api.get(
        `/sequences/product-revisions/${productRevisionId}/production-release`,
      )
    ).data;
  },
};
