import api from "./api";

export type DataRow = Record<string, any>;

export interface RevisionDetail {
  revision: DataRow;
  parts: DataRow[];
  weld_joints: DataRow[];
  requirements: DataRow[];
  validation: { can_approve: boolean; risks: DataRow[] };
  preview_url: string;
}

export const engineeringService = {
  async projects(): Promise<DataRow[]> {
    return (await api.get("/engineering/projects")).data;
  },
  async createProject(data: DataRow): Promise<DataRow> {
    return (await api.post("/engineering/projects", data)).data;
  },
  async deleteProject(projectId: string): Promise<void> {
    await api.delete(`/engineering/projects/${projectId}`);
  },
  async products(projectId: string): Promise<DataRow[]> {
    return (await api.get(`/engineering/projects/${projectId}/products`)).data;
  },
  async createProduct(projectId: string, data: DataRow): Promise<DataRow> {
    return (await api.post(`/engineering/projects/${projectId}/products`, data))
      .data;
  },
  async revisions(productId: string): Promise<DataRow[]> {
    return (await api.get(`/engineering/products/${productId}/revisions`)).data;
  },
  async uploadDrawing(
    productId: string,
    file: File,
    summary?: string,
  ): Promise<DataRow> {
    const form = new FormData();
    form.append("file", file);
    if (summary) form.append("change_summary", summary);
    return (await api.post(`/engineering/products/${productId}/drawings`, form))
      .data;
  },
  async detail(revisionId: string): Promise<RevisionDetail> {
    return (await api.get(`/engineering/revisions/${revisionId}`)).data;
  },
  async deleteRevision(revisionId: string): Promise<void> {
    await api.delete(`/engineering/revisions/${revisionId}`);
  },
  async preview(revisionId: string, page: number): Promise<Blob> {
    return (
      await api.get(
        `/engineering/revisions/${revisionId}/pages/${page}/preview`,
        { responseType: "blob" },
      )
    ).data;
  },
  async parse(
    revisionId: string,
    data: DataRow = { mode: "platform", run_ocr: true },
  ): Promise<DataRow> {
    return (await api.post(`/engineering/revisions/${revisionId}/parse`, data))
      .data;
  },
  async patchPart(id: string, values: DataRow): Promise<DataRow> {
    return (await api.patch(`/engineering/parts/${id}`, { values })).data;
  },
  async patchProductIdentity(revisionId: string, values: DataRow): Promise<DataRow> {
    return (
      await api.patch(`/engineering/revisions/${revisionId}/product-identity`, {
        values,
      })
    ).data;
  },
  async patchJoint(id: string, values: DataRow): Promise<DataRow> {
    return (await api.patch(`/engineering/weld-joints/${id}`, { values })).data;
  },
  async patchRequirement(id: string, values: DataRow): Promise<DataRow> {
    return (await api.patch(`/engineering/requirements/${id}`, { values }))
      .data;
  },
  async addJoint(revisionId: string, values: DataRow): Promise<DataRow> {
    return (
      await api.post(`/engineering/revisions/${revisionId}/weld-joints`, values)
    ).data;
  },
  async deleteJoint(id: string): Promise<void> {
    await api.delete(`/engineering/weld-joints/${id}`);
  },
  async splitJoint(id: string, values: DataRow): Promise<DataRow[]> {
    return (await api.post(`/engineering/weld-joints/${id}/split`, values))
      .data;
  },
  async mergeJoints(revisionId: string, values: DataRow): Promise<DataRow> {
    return (
      await api.post(
        `/engineering/revisions/${revisionId}/weld-joints/merge`,
        values,
      )
    ).data;
  },
  async approve(revisionId: string, force = false): Promise<DataRow> {
    return (
      await api.post(`/engineering/revisions/${revisionId}/approve`, { force })
    ).data;
  },
  async history(revisionId: string): Promise<DataRow[]> {
    return (await api.get(`/engineering/revisions/${revisionId}/history`)).data;
  },
};
