"""Scoped drawing extraction, durable stage checkpoints and coverage evidence."""
from collections import Counter
from copy import deepcopy

from app.services.ai_provider_service import AIProviderResult

PIPELINE_VERSION = "drawing-v4-full-title"


class CheckpointProvider:
    def __init__(self, provider, job, db, validator):
        self.provider, self.job, self.db, self.validator = provider, job, db, validator

    def structured_response(self, request):
        key = request.schema_name
        cached = (self.job.progress_detail or {}).get("checkpoints", {}).get(key)
        if cached is not None:
            self.validator(cached, request.json_schema)
            return AIProviderResult(deepcopy(cached), None, 0, 0, 0)
        result = self.provider.structured_response(request)
        self.job.input_tokens = (self.job.input_tokens or 0) + result.input_tokens
        self.job.output_tokens = (self.job.output_tokens or 0) + result.output_tokens
        self.job.total_tokens = (self.job.total_tokens or 0) + result.total_tokens
        self.db.commit()
        self.validator(result.data, request.json_schema)
        detail = deepcopy(self.job.progress_detail or {})
        detail.setdefault("checkpoints", {})[key] = deepcopy(result.data)
        self.job.progress_detail = detail
        self.db.commit()
        return result


def completeness_report(revision, parts, joints):
    metadata = revision.drawing_metadata or {}
    coverage = metadata.get("recognition_coverage") or {}
    total = revision.drawing_page_count or 0
    recognized = sorted(set(coverage.get("pages") or []))
    names = Counter(j.weld_number for j in joints if j.weld_number)
    missing_evidence = []
    for kind, rows in (("part", parts), ("weld", joints)):
        for item in rows:
            evidence = item.evidence or {}
            if not evidence.get("page") or not evidence.get("bbox"):
                missing_evidence.append(
                    {
                        "kind": kind,
                        "id": item.id,
                        "label": getattr(item, "weld_number", None)
                        or getattr(item, "name", None),
                    }
                )
    product = metadata.get("extracted_product") or {}
    for field in ("drawing_number", "product_name"):
        evidence = (product.get("evidence") or {}).get(field) or {}
        if product.get(field) and (
            not evidence.get("page") or not evidence.get("bbox")
        ):
            missing_evidence.append({"kind": "product", "label": field})
    return {
        "total_pages": total,
        "recognized_pages": recognized,
        "unrecognized_pages": [n for n in range(1, total + 1) if n not in recognized],
        "weld_count": len(joints),
        "part_count": len(parts),
        "duplicate_weld_numbers": sorted(n for n, count in names.items() if count > 1),
        "unresolved_connections": [
            j.weld_number for j in joints if not j.part_a_id or not j.part_b_id
        ],
        "unknown_quantities": [p.name for p in parts if p.quantity is None],
        "missing_evidence": missing_evidence,
        "unresolved_regions": coverage.get("unresolved_regions") or [],
        "notice": "识别数量不是图纸实际总数；未覆盖页和未解析区域须人工核对是否漏项。",
    }
