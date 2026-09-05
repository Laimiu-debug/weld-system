"""P3 engineering projects, drawing extraction, and visual review APIs."""
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.smart_import import (
    resolve_workspace,
    validate_ai_extraction_request,
)
from app.core.data_access import WorkspaceType
from app.core.module_permissions import ensure_module_permission
from app.models.engineering import Part, ProductRevision, WeldJoint, WeldRequirement
from app.models.smart_import import SourceDocument
from app.models.user import User
from app.schemas.engineering import (
    DrawingAIRequest,
    EntityPatch,
    JointCreate,
    JointMerge,
    JointSplit,
    ProductCreate,
    ProjectCreate,
    RevisionApprove,
)
from app.services.ai_credential_service import (
    AIProviderConfigService,
    resolve_platform_ai_config,
)
from app.services.ai_extraction_service import AIExtractionRunError, build_provider
from app.services.document_page_renderer import DocumentPageRenderer
from app.services.document_parser_service import DocumentParseError
from app.services.document_storage_service import (
    DocumentStorage,
    DocumentUploadError,
    get_document_storage,
)
from app.services.engineering_service import EngineeringService
from app.services.ai_quota_service import AIQuotaError
from app.services.operations_service import OperationsService
from app.services.system_config_service import get_max_upload_bytes
from app.services.ai_extraction_queue_service import AIExtractionQueueService
from app.services.ai_routing_service import routing_snapshot, require_expected_route
from app.api.v1.endpoints.smart_import import (
    resolve_platform_provider_config,
    resolve_offline_provider_config,
    dispatch_extraction_job,
)
from app.models.smart_import import ExtractionJob
from app.schemas.smart_import import ExtractionJobResponse
from datetime import datetime

router = APIRouter()


@router.get("/drawing-capabilities")
def drawing_capabilities(current_user: User = Depends(deps.get_current_active_user)):
    from app.services.cad_conversion_service import cad_capabilities

    return cad_capabilities()


@router.get("/revisions/{revision_id}/parse-jobs")
def drawing_jobs(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    EngineeringService(db)._get(ProductRevision, revision_id, current_user, context)
    jobs = (
        db.query(ExtractionJob)
        .filter(
            ExtractionJob.schema_snapshot["drawing_revision_id"].astext == revision_id
        )
        .order_by(ExtractionJob.created_at.desc())
        .limit(20)
        .all()
    )
    return [ExtractionJobResponse.model_validate(job) for job in jobs]


@router.post("/revisions/{revision_id}/parse-async", status_code=202)
def queue_drawing(
    revision_id: str,
    request: DrawingAIRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "create")
    validate_ai_extraction_request(request)
    if request.extracted_payload is not None or (
        request.mode == "byok" and not request.provider_config_id
    ):
        raise HTTPException(422, "后台识别仅支持平台、离线模型或已保存的模型配置")
    revision = EngineeringService(db)._get(
        ProductRevision, revision_id, current_user, context, True
    )
    revision = (
        db.query(ProductRevision)
        .filter(ProductRevision.id == revision.id)
        .populate_existing()
        .with_for_update()
        .one()
    )
    if revision.status in {"approved", "superseded"}:
        raise HTTPException(409, "已批准版本不可重新解析，请上传新图纸版本")
    if revision.parse_status == "processing":
        raise HTTPException(409, "图纸已有正在执行的识别任务")
    document = (
        db.query(SourceDocument)
        .filter(SourceDocument.id == revision.drawing_document_id)
        .one()
    )
    credentials = AIProviderConfigService(db)
    if request.provider_config_id:
        config, _ = credentials.resolve_for_use(
            request.provider_config_id, current_user, context
        )
    else:
        credentials.enforce_policy(request.mode, None, context)
        config = (
            resolve_offline_provider_config(db, context)
            if request.mode == "offline"
            else resolve_platform_provider_config(db, document)[0]
        )
    if request.mode != "offline":
        if request.mode == "platform":
            require_expected_route(request.expected_platform_route, config)
        OperationsService(db).require_consent(
            document.id,
            config.base_url,
            current_user,
            context,
            request.outbound_consent_id,
        )
    from copy import deepcopy
    from app.services.drawing_review_service import PIPELINE_VERSION
    route = routing_snapshot(config, "drawing_import", "advanced")
    options = {"page_numbers": request.page_numbers, "region": request.region,
               "page_rotations": {str(k): v for k, v in request.page_rotations.items()},
               "pipeline_version": PIPELINE_VERSION}
    checkpoints = {}
    if request.retry_job_id:
        old = db.query(ExtractionJob).filter(ExtractionJob.id == request.retry_job_id).first()
        snapshot = old.schema_snapshot or {} if old else {}
        if (not old or snapshot.get("drawing_revision_id") != revision.id
            or old.status not in {"failed", "cancelled"}
            or snapshot.get("source_data_version") != revision.data_version
            or snapshot.get("x-weld-routing") != route or old.mode != request.mode
            or old.provider_config_id != request.provider_config_id
            or (snapshot.get("drawing_options") or {}).get("pipeline_version") != PIPELINE_VERSION):
            raise HTTPException(409, "原任务、图纸版本或模型配置已变化，请重新识别")
        options = deepcopy(snapshot["drawing_options"])
        checkpoints = deepcopy((old.progress_detail or {}).get("checkpoints") or {})
    if any(n > revision.drawing_page_count for n in (options.get("page_numbers") or [])) or any(int(n) > revision.drawing_page_count for n in options.get("page_rotations", {})):
        raise HTTPException(422, "识别页码超过图纸页数")
    prior_parse_status = revision.parse_status
    revision.parse_status = "processing"
    try:
        job = AIExtractionQueueService(db).create_job(
            document_id=document.id,
            schema_snapshot={
                "schema_version": "drawing-v3",
                "drawing_options": options,
                "prior_parse_status": prior_parse_status,
                "retry_job_id": request.retry_job_id,
                "job_kind": "drawing",
                "drawing_revision_id": revision.id,
                "actor_user_id": current_user.id,
                "source_data_version": revision.data_version,
                "outbound_consent_id": request.outbound_consent_id,
                "x-weld-routing": routing_snapshot(
                    config, "drawing_import", "advanced"
                ),
            },
            template_id=None,
            mode=request.mode,
            provider=config.provider,
            model=config.model,
            provider_config_id=request.provider_config_id,
            run_ocr=True,
            user=current_user,
            context=context,
        )
    except Exception:
        db.rollback()
        raise
    job.progress_detail = {**(job.progress_detail or {}), "job_kind": "drawing",
        "scope": options, "checkpoints": checkpoints,
        "pages": {"completed": 0, "total": len(options.get("page_numbers") or []) or revision.drawing_page_count}}
    db.commit()
    try:
        dispatch_extraction_job(job)
    except HTTPException:
        job.status = "failed"
        job.error_code = "queue_unavailable"
        job.error_message = "后台任务队列不可用，请稍后重试"
        job.completed_at = datetime.utcnow()
        revision.parse_status = "failed"
        db.commit()
        raise
    return {"job": ExtractionJobResponse.model_validate(job)}


def permitted(db, user, context, action="view"):
    if context.workspace_type == WorkspaceType.ENTERPRISE:
        ensure_module_permission(db, user, "engineering", action)


def row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


def extracted_row(item):
    """Serialize legacy and current extracted rows with an explicit provenance."""
    value = row(item)
    evidence = dict(value.get("evidence") or {})
    if not evidence.get("source"):
        evidence["source"] = (
            "manual_correction"
            if value.get("review_status") == "corrected"
            else "ai_extraction"
        )
    evidence.setdefault("source_document_id", None)
    value["evidence"] = evidence
    return value


@router.get("/projects")
def projects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    result = []
    for item in EngineeringService(db).list_projects(current_user, context):
        value = row(item)
        value["products"] = len(
            EngineeringService(db).list_products(item.id, current_user, context)
        )
        result.append(value)
    return result


@router.post("/projects", status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "create")
    return row(EngineeringService(db).create_project(data, current_user, context))


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "delete")
    EngineeringService(db).delete_project(project_id, current_user, context, storage)


@router.get("/projects/{project_id}/products")
def products(
    project_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    return [
        row(x)
        for x in EngineeringService(db).list_products(project_id, current_user, context)
    ]


@router.post("/projects/{project_id}/products", status_code=201)
def create_product(
    project_id: str,
    data: ProductCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "create")
    return row(
        EngineeringService(db).create_product(project_id, data, current_user, context)
    )


@router.get("/products/{product_id}/revisions")
def product_revisions(
    product_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    return [
        row(x)
        for x in EngineeringService(db).list_revisions(
            product_id, current_user, context
        )
    ]


@router.post("/products/{product_id}/drawings", status_code=201)
def upload_drawing(
    product_id: str,
    file: UploadFile = File(...),
    change_summary: str | None = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "create")
    try:
        from pathlib import Path
        from app.services.cad_conversion_service import cad_capabilities

        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in cad_capabilities()["extensions"]:
            raise HTTPException(
                422, "当前服务器不支持此图纸格式；DWG 需要可用的 ODA 转换器，请导出 PDF 或 DXF 后上传"
            )
        return row(
            EngineeringService(db).upload_drawing(
                product_id,
                file.file,
                file.filename or "drawing.pdf",
                current_user,
                context,
                storage,
                get_max_upload_bytes(),
                change_summary,
            )
        )
    except DocumentUploadError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        file.file.close()


@router.get("/revisions/{revision_id}")
def revision_detail(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    rev, parts, joints, reqs, validation = EngineeringService(db).get_revision(
        revision_id, current_user, context
    )
    return {
        "revision": row(rev),
        "parts": [extracted_row(x) for x in parts],
        "weld_joints": [extracted_row(x) for x in joints],
        "requirements": [extracted_row(x) for x in reqs],
        "validation": validation,
        "preview_url": f"/engineering/revisions/{rev.id}/pages/1/preview",
    }


@router.delete("/revisions/{revision_id}", status_code=204)
def delete_revision(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "delete")
    EngineeringService(db).delete_revision(revision_id, current_user, context, storage)


@router.get("/revisions/{revision_id}/pages/{page_number}/preview")
def drawing_preview(
    revision_id: str,
    page_number: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    rev = EngineeringService(db)._get(
        ProductRevision, revision_id, current_user, context
    )
    if page_number < 1 or page_number > rev.drawing_page_count:
        raise HTTPException(404, "图纸页码不存在")
    document = (
        db.query(SourceDocument)
        .filter(SourceDocument.id == rev.drawing_document_id)
        .one()
    )
    try:
        with storage.open_stream(document.storage_key) as stream:
            data = DocumentPageRenderer().render_png(
                stream, document.original_filename, page_number
            )
    except DocumentParseError as exc:
        raise HTTPException(422, str(exc)) from exc
    return StreamingResponse(
        BytesIO(data),
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.post("/revisions/{revision_id}/parse")
def parse_drawing(
    revision_id: str,
    request: DrawingAIRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "create")
    if request.page_numbers or request.region or request.page_rotations or request.retry_job_id:
        raise HTTPException(422, "局部识别、方向设置和阶段重试请使用后台识别接口")
    provider = None
    config = None
    try:
        if request.extracted_payload is None:
            validate_ai_extraction_request(request)
            credentials = AIProviderConfigService(db)
            key = None
            if request.provider_config_id:
                config, key = credentials.resolve_for_use(
                    request.provider_config_id, current_user, context
                )
            else:
                credentials.enforce_policy(request.mode, None, context)
                if request.mode == "platform":
                    platform = resolve_platform_ai_config(
                        db,
                        include_key=True,
                        task_type="drawing_import",
                        complexity="advanced",
                    )
                    if not platform["key_configured"] or not platform["model"]:
                        raise HTTPException(status_code=503, detail="平台 AI 服务尚未配置")
                    from types import SimpleNamespace

                    config = SimpleNamespace(
                        id=platform["id"],
                        provider=platform["provider"],
                        base_url=platform["base_url"],
                        model=platform["model"],
                        complexity_level=platform.get("complexity_level") or "advanced",
                        point_multiplier=float(platform.get("point_multiplier") or 1),
                    )
                    key = platform["api_key"]
            revision = EngineeringService(db)._get(
                ProductRevision, revision_id, current_user, context
            )
            if request.mode != "offline":
                if request.mode == "platform":
                    require_expected_route(request.expected_platform_route, config)
                provider_url = (
                    config.base_url if config is not None else request.base_url
                )
                if not provider_url:
                    raise HTTPException(422, "外部模型服务地址不能为空")
                OperationsService(db).require_consent(
                    revision.drawing_document_id,
                    provider_url,
                    current_user,
                    context,
                    request.outbound_consent_id,
                )
            provider = build_provider(request, config, key)
        run = EngineeringService(db).parse_revision(
            revision_id,
            request.extracted_payload,
            provider,
            request.mode,
            config.id if config and request.mode == "byok" else None,
            current_user,
            context,
            storage,
            float(getattr(config, "point_multiplier", 1) or 1),
            {
                "config_id": getattr(config, "id", None),
                "task_type": "drawing_import",
                "complexity": getattr(config, "complexity_level", "advanced"),
                "point_multiplier": float(getattr(config, "point_multiplier", 1) or 1),
            },
        )
        return row(run)
    except AIExtractionRunError as exc:
        raise HTTPException(
            exc.status_code, {"code": exc.code, "message": str(exc)}
        ) from exc
    except AIQuotaError as exc:
        raise HTTPException(
            exc.status_code, {"code": exc.code, "message": str(exc)}
        ) from exc
    finally:
        if provider is not None:
            provider.close()


@router.patch("/parts/{entity_id}")
def patch_part(
    entity_id: str,
    data: EntityPatch,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    entity, rev = EngineeringService(db).patch_entity(
        Part, entity_id, data.values, data.reason, current_user, context
    )
    return {"entity": row(entity), "revision": row(rev)}


@router.patch("/revisions/{revision_id}/product-identity")
def patch_product_identity(
    revision_id: str,
    data: EntityPatch,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    revision = EngineeringService(db).patch_product_identity(
        revision_id, data.values, data.reason, current_user, context
    )
    return row(revision)


@router.patch("/weld-joints/{entity_id}")
def patch_joint(
    entity_id: str,
    data: EntityPatch,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    entity, rev = EngineeringService(db).patch_entity(
        WeldJoint, entity_id, data.values, data.reason, current_user, context
    )
    return {"entity": row(entity), "revision": row(rev)}


@router.patch("/requirements/{entity_id}")
def patch_requirement(
    entity_id: str,
    data: EntityPatch,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    entity, rev = EngineeringService(db).patch_entity(
        WeldRequirement, entity_id, data.values, data.reason, current_user, context
    )
    return {"entity": row(entity), "revision": row(rev)}


@router.post("/revisions/{revision_id}/weld-joints", status_code=201)
def add_joint(
    revision_id: str,
    data: JointCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    return row(
        EngineeringService(db).add_joint(revision_id, data, current_user, context)
    )


@router.delete("/weld-joints/{joint_id}", status_code=204)
def delete_joint(
    joint_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "delete")
    EngineeringService(db).delete_joint(joint_id, current_user, context)


@router.post("/weld-joints/{joint_id}/split")
def split_joint(
    joint_id: str,
    data: JointSplit,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    return [
        row(x)
        for x in EngineeringService(db).split_joint(
            joint_id,
            data.weld_numbers,
            data.lengths_mm,
            data.reason,
            current_user,
            context,
        )
    ]


@router.post("/revisions/{revision_id}/weld-joints/merge")
def merge_joints(
    revision_id: str,
    data: JointMerge,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "edit")
    return row(
        EngineeringService(db).merge_joints(
            revision_id,
            data.joint_ids,
            data.weld_number,
            data.reason,
            current_user,
            context,
        )
    )


@router.get("/revisions/{revision_id}/validation")
def validate_revision(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    return EngineeringService(db).validate_revision(revision_id, current_user, context)


@router.post("/revisions/{revision_id}/approve")
def approve_revision(
    revision_id: str,
    data: RevisionApprove,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context, "approve")
    return row(
        EngineeringService(db).approve_revision(
            revision_id, data.force, data.note, current_user, context
        )
    )


@router.get("/revisions/{revision_id}/history")
def history(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    permitted(db, current_user, context)
    return [
        row(x)
        for x in EngineeringService(db).history(revision_id, current_user, context)
    ]
