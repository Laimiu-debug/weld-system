"""Document classification, template recommendation, and supporting-PQR matching."""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.pqr import PQR
from app.models.smart_import import ExtractedEntity, ExtractedField
from app.models.user import User
from app.services.smart_import_service import SmartImportService
from app.services.wps_template_service import WPSTemplateService


_TYPE_MARKERS = {
    "pqr": ("procedure qualification record", "工艺评定记录", "pqr", "wpqr"),
    "wps": ("welding procedure specification", "焊接工艺规程", "wps"),
    "ppqr": ("preliminary welding procedure", "预焊接工艺规程", "ppqr", "pwps"),
    "welder": ("welder qualification", "焊工资格", "焊工证", "welder certificate"),
}
_PROCESS_MARKERS = (
    "smaw",
    "gtaw",
    "gmaw",
    "fcaw",
    "saw",
    "111",
    "121",
    "135",
    "136",
    "138",
    "141",
)
_STANDARD_PATTERNS = (
    r"ASME\s*(?:SECTION\s*)?IX",
    r"AWS\s*D\s*1\.1",
    r"ISO\s*156(?:09|14)[\w\-\.]*",
    r"GB(?:/T|/Z|\s*T)?\s*\d+[\w\-\.]*",
    r"NB/T\s*\d+[\w\-\.]*",
)


class SmartImportTemplateService:
    def __init__(self, db: Session):
        self.db = db
        self.smart_import = SmartImportService(db)

    def recommend_for_document(
        self,
        document_id: str,
        user: User,
        context: WorkspaceContext,
    ) -> dict[str, Any]:
        document = self.smart_import.get_document(document_id, user, context)
        pages = self.smart_import.get_document_pages(document.id, user, context)
        text = "\n".join(page.text_content or "" for page in pages)[:100_000]
        classification = self.classify(text, document.document_type)
        templates, _ = WPSTemplateService(self.db).get_available_templates(
            current_user=user,
            workspace_context=context,
            module_type=classification["document_type"],
            limit=100,
        )
        recommendations = []
        normalized = text.casefold()
        for template in templates:
            score = 20
            reasons = ["类型一致"]
            process = str(template.welding_process or "").strip()
            standard = str(template.standard or "").strip()
            if process and process.casefold() in normalized:
                score += 45
                reasons.append(f"识别到焊接方法 {process}")
            if standard and self._loosely_contains(normalized, standard):
                score += 35
                reasons.append(f"识别到标准 {standard}")
            score += min(int(template.usage_count or 0), 10)
            recommendations.append(
                {
                    "template_id": template.id,
                    "name": template.name,
                    "score": min(score, 100),
                    "reasons": reasons,
                    "welding_process": template.welding_process,
                    "standard": template.standard,
                }
            )
        recommendations.sort(key=lambda item: (-item["score"], item["name"]))
        return {
            "classification": classification,
            "recommendations": recommendations[:5],
        }

    @staticmethod
    def classify(text: str, declared_type: str = "unknown") -> dict[str, Any]:
        normalized = text.casefold()
        scores = {
            kind: sum(1 for marker in markers if marker.casefold() in normalized)
            for kind, markers in _TYPE_MARKERS.items()
        }
        best = max(scores, key=scores.get) if any(scores.values()) else declared_type
        if best not in _TYPE_MARKERS:
            best = "unknown"
        declared_bonus = 1 if declared_type == best else 0
        evidence_count = scores.get(best, 0) + declared_bonus
        confidence = (
            min(0.55 + evidence_count * 0.12, 0.98) if best != "unknown" else 0.25
        )
        processes = [value.upper() for value in _PROCESS_MARKERS if value in normalized]
        standards = []
        for pattern in _STANDARD_PATTERNS:
            standards.extend(
                match.group(0).strip() for match in re.finditer(pattern, text, re.I)
            )
        return {
            "document_type": best,
            "confidence": round(confidence, 2),
            "declared_type": declared_type,
            "detected_processes": list(dict.fromkeys(processes))[:10],
            "detected_standards": list(dict.fromkeys(standards))[:10],
            "requires_confirmation": best == "unknown" or confidence < 0.75,
        }

    def match_supporting_pqrs(
        self,
        entity: ExtractedEntity,
        user: User,
        context: WorkspaceContext,
    ) -> list[dict[str, Any]]:
        if entity.entity_type != "wps":
            return []
        values = {
            field.field_key: field.normalized_value
            for field in self.db.query(ExtractedField)
            .filter(ExtractedField.entity_id == entity.id)
            .all()
            if field.normalized_value not in (None, "")
        }
        query = self.db.query(PQR).filter(PQR.is_active == True)
        if context.workspace_type == WorkspaceType.PERSONAL:
            query = query.filter(
                PQR.user_id == user.id, PQR.workspace_type == "personal"
            )
        else:
            query = query.filter(
                PQR.company_id == context.company_id, PQR.workspace_type == "enterprise"
            )
        candidates = []
        for pqr in query.order_by(PQR.updated_at.desc()).limit(200).all():
            score = 0
            reasons = []
            for key, weight, label in (
                ("welding_process", 35, "焊接方法"),
                ("process_specification", 25, "标准"),
                ("base_material_group", 20, "母材组别"),
                ("base_material_spec", 10, "母材牌号"),
            ):
                wanted = str(values.get(key) or "").casefold().strip()
                actual = str(getattr(pqr, key, None) or "").casefold().strip()
                if wanted and actual and (wanted in actual or actual in wanted):
                    score += weight
                    reasons.append(f"{label}一致")
            if pqr.status == "approved":
                score += 10
                reasons.append("PQR 已批准")
            if score:
                candidates.append(
                    {
                        "pqr_id": pqr.id,
                        "pqr_number": pqr.pqr_number,
                        "title": pqr.title,
                        "status": pqr.status,
                        "score": min(score, 100),
                        "reasons": reasons,
                        "eligible": pqr.status == "approved",
                    }
                )
        return sorted(
            candidates, key=lambda item: (-item["score"], item["pqr_number"])
        )[:10]

    @staticmethod
    def _loosely_contains(text: str, value: str) -> bool:
        compact_text = re.sub(r"[^a-z0-9]", "", text.casefold())
        compact_value = re.sub(r"[^a-z0-9]", "", value.casefold())
        return bool(compact_value and compact_value in compact_text)
