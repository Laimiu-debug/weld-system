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
from app.services.document_storage_service import (
    DocumentStorage,
    DocumentUploadError,
    get_document_storage,
)
from app.services.engineering_service import EngineeringService
from app.services.system_config_service import get_max_upload_bytes

router = APIRouter()


def permitted(db, user, context, action="view"):
    if context.workspace_type == WorkspaceType.ENTERPRISE:
        ensure_module_permission(db, user, "engineering", action)


def row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


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
    EngineeringService(db).delete_project(
        project_id, current_user, context, storage
    )


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
        "parts": [row(x) for x in parts],
        "weld_joints": [row(x) for x in joints],
        "requirements": [row(x) for x in reqs],
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
    EngineeringService(db).delete_revision(
        revision_id, current_user, context, storage
    )


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
    with storage.open_stream(document.storage_key) as stream:
        data = DocumentPageRenderer().render_png(
            stream, document.original_filename, page_number
        )
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
                        id=None,
                        provider=platform["provider"],
                        base_url=platform["base_url"],
                        model=platform["model"],
                        complexity_level=platform.get("complexity_level")
                        or "advanced",
                        point_multiplier=float(
                            platform.get("point_multiplier") or 1
                        ),
                    )
                    key = platform["api_key"]
            provider = build_provider(request, config, key)
        run = EngineeringService(db).parse_revision(
            revision_id,
            request.extracted_payload,
            provider,
            request.mode,
            config.id if config else None,
            current_user,
            context,
            storage,
            float(getattr(config, "point_multiplier", 1) or 1),
            {
                "config_id": getattr(config, "id", None),
                "task_type": "drawing_import",
                "complexity": getattr(config, "complexity_level", "advanced"),
                "point_multiplier": float(
                    getattr(config, "point_multiplier", 1) or 1
                ),
            },
        )
        return row(run)
    except AIExtractionRunError as exc:
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
