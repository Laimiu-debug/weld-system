"""Opt-in real-provider acceptance in an isolated local PostgreSQL schema.

Uses the application's saved encrypted model configuration, ingestion, consent,
queue and worker services. Only broker dispatch and DB/storage locations are
substituted; provider HTTP requests, parsing, validation and persistence are real.
Private output must be outside the repository. No credentials are exported.
"""
import argparse
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import re
import sys
import time
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import app.models
from app.core.database import Base, engine, SessionLocal
from app.core.data_access import WorkspaceContext
from app.models.user import User
from app.models.smart_import import (
    AIProviderConfig,
    AIPlanEntitlement,
    ExtractionJob,
    DocumentPage,
    ExtractedEntity,
    ExtractedField,
    FieldEvidence,
)
from app.models.engineering import DrawingParseRun, Part, WeldJoint, WeldRequirement
from app.schemas.engineering import ProjectCreate, ProductCreate, DrawingAIRequest
from app.schemas.smart_import import (
    ImportBatchCreate,
    SourceDocumentRegister,
    AIExtractionRequest,
)
from app.schemas.operations import OutboundConsentCreate
from app.services.engineering_service import EngineeringService
from app.services.smart_import_service import SmartImportService
from app.services.operations_service import OperationsService
from app.services.document_storage_service import LocalDocumentStorage
from app.services.document_parser_service import DefaultDocumentParser
from app.services.ai_routing_service import route_fingerprint
from app.api.v1.endpoints.engineering import queue_drawing
from app.api.v1.endpoints.smart_import import queue_document_extraction
from app.tasks import smart_import_tasks as worker


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["drawing", "pqr", "docx", "cleanup"])
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config-id", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    assert not args.output.resolve().is_relative_to(
        repo
    ), "Private output must stay outside repository"
    assert engine.url.host in {"localhost", "127.0.0.1"}, "Local PostgreSQL only"
    engine.echo = False
    args.output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=args.output / "worker.log", level=logging.WARNING)
    state_path = args.output / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["config_id"] == args.config_id
    else:
        assert args.phase != "cleanup"
        state = {
            "schema": "qa_ai06_" + uuid4().hex[:12],
            "config_id": args.config_id,
            "created_at": datetime.now().isoformat(),
            "documents": {},
            "jobs": [],
        }
    schema = state["schema"]
    assert re.fullmatch(r"qa_ai06_[a-f0-9]{12}", schema)
    admin = create_engine(engine.url, echo=False)
    if args.phase == "cleanup":
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        state["cleaned_at"] = datetime.now().isoformat()
        write_json(state_path, state)
        print("Isolated acceptance database cleaned; private report retained.")
        return 0
    assert not state.get("cleaned_at"), "Use a new output directory after cleanup"
    with SessionLocal() as source:
        config = source.get(AIProviderConfig, args.config_id)
        assert config and config.is_active and config.last_test_status == "success"
        config_values = {
            key: getattr(config, key)
            for key in [
                "id",
                "scope_type",
                "name",
                "provider",
                "base_url",
                "model",
                "encrypted_api_key",
                "key_last_four",
                "key_version",
                "task_types",
                "complexity_level",
                "point_multiplier",
                "is_default",
                "priority",
                "is_active",
                "last_test_status",
                "last_tested_at",
            ]
        }
    if not state_path.exists():
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        write_json(state_path, state)
    local = create_engine(
        engine.url,
        echo=False,
        connect_args={"options": f"-c search_path={schema} -c lock_timeout=10000"},
    )
    with local.begin() as conn:
        assert conn.execute(text("SELECT current_schema()")).scalar() == schema
        Base.metadata.create_all(conn)
    sessions = sessionmaker(local, autoflush=False, expire_on_commit=False)
    storage = LocalDocumentStorage(args.output / "storage")
    with sessions() as db:
        if not state.get("user_id"):
            owner = User(
                email=f"{uuid4().hex}@example.invalid",
                username=uuid4().hex,
                hashed_password="!disabled",
                is_active=True,
                member_tier="free",
                membership_type="personal",
            )
            db.add(owner)
            db.add(AIProviderConfig(**config_values))
            db.add(
                AIPlanEntitlement(
                    tier_key="free",
                    workspace_type="personal",
                    daily_points=10000,
                    monthly_points=10000,
                    max_points_per_task=1000,
                    max_pages_per_task=30,
                    max_tasks_per_day=50,
                    max_tasks_per_month=50,
                    max_concurrent_tasks=3,
                    max_user_tasks_per_day=50,
                    max_user_tasks_per_month=50,
                    max_user_concurrent_tasks=3,
                    is_enabled=True,
                )
            )
            db.commit()
            state["user_id"] = owner.id
            write_json(state_path, state)
        owner = db.get(User, state["user_id"])
        context = WorkspaceContext(user_id=owner.id, workspace_type="personal")
        smart = SmartImportService(db)
        entry = state["documents"].get(args.phase)
        if not entry:
            filename = {
                "drawing": "26047-100立方米XAI液化缓冲罐.pdf",
                "pqr": "HGP-20-486.pdf",
                "docx": "HGP-21-622B.docx",
            }[args.phase]
            path = args.samples / filename
            if args.phase == "drawing":
                service = EngineeringService(db)
                project = service.create_project(
                    ProjectCreate(code=uuid4().hex, name="AI06 acceptance"),
                    owner,
                    context,
                )
                product = service.create_product(
                    project.id,
                    ProductCreate(code=uuid4().hex, name="AI06 acceptance"),
                    owner,
                    context,
                )
                with path.open("rb") as stream:
                    rev = service.upload_drawing(
                        product.id,
                        stream,
                        filename,
                        owner,
                        context,
                        storage,
                        50 * 1024 * 1024,
                    )
                entry = {
                    "document_id": rev.drawing_document_id,
                    "revision_id": rev.id,
                    "filename": filename,
                }
            else:
                batch = smart.create_batch(
                    ImportBatchCreate(
                        name="AI06 " + args.phase, target_entity_type="pqr"
                    ),
                    owner,
                    context,
                )
                with path.open("rb") as stream:
                    stored = storage.save_stream(stream, filename, 50 * 1024 * 1024)
                doc = smart.register_document(
                    batch.id,
                    SourceDocumentRegister(
                        original_filename=filename,
                        sha256=stored.sha256,
                        storage_key=stored.storage_key,
                        size_bytes=stored.size_bytes,
                        mime_type=stored.mime_type,
                        document_type="pqr",
                    ),
                    owner,
                    context,
                )
                smart.parse_document(
                    doc.id, owner, context, storage, DefaultDocumentParser()
                )
                entry = {"document_id": doc.id, "filename": filename}
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            state["documents"][args.phase] = entry
            write_json(state_path, state)
        notice = "User authorized AI06 acceptance of supplied drawing and PQR samples using the specified DeepSeek vision model."
        consent = OperationsService(db).create_consent(
            OutboundConsentCreate(
                document_id=entry["document_id"],
                provider_host="api.deepseek.com",
                purpose="AI06 用户指定真实样本验收",
                privacy_notice_version="ai-data-outbound-v1",
                privacy_notice_hash=hashlib.sha256(notice.encode()).hexdigest(),
                authorized=True,
            ),
            owner,
            context,
        )
        request = {
            "mode": "platform",
            "outbound_consent_id": consent.id,
            "expected_platform_route": route_fingerprint(config_values),
        }
        if args.phase == "drawing":
            with patch("app.api.v1.endpoints.engineering.dispatch_extraction_job"):
                result = queue_drawing(
                    entry["revision_id"], DrawingAIRequest(**request), db, owner, None
                )
                job_id = result["job"].id
        else:
            with patch("app.api.v1.endpoints.smart_import.dispatch_extraction_job"):
                result = queue_document_extraction(
                    entry["document_id"],
                    AIExtractionRequest(**request),
                    db,
                    owner,
                    None,
                )
                job_id = result.job.id
        state["jobs"].append({"phase": args.phase, "id": job_id})
        write_json(state_path, state)
    calls = []
    build = worker.build_provider

    def traced_build(*a, **kw):
        provider = build(*a, **kw)
        send = provider.structured_response

        def trace(request):
            started = time.monotonic()
            print(
                f"{args.phase}: model call {len(calls)+1}, schema={request.schema_name}, images={len(request.images)}",
                flush=True,
            )
            value = send(request)
            calls.append(
                {
                    "schema": request.schema_name,
                    "images": len(request.images),
                    "seconds": round(time.monotonic() - started, 2),
                    "tokens": value.total_tokens,
                    "response_id": value.response_id,
                    "data": value.data,
                }
            )
            write_json(args.output / f"{job_id}-calls.json", calls)
            return value

        provider.structured_response = trace
        return provider

    with patch.object(worker, "SessionLocal", sessions), patch.object(
        worker, "get_document_storage", return_value=storage
    ), patch.object(worker, "build_provider", traced_build):
        worker.run_smart_import_extraction.run(job_id)
    with sessions() as db:
        job = db.get(ExtractionJob, job_id)
        report = {
            "job_id": job_id,
            "phase": args.phase,
            "status": job.status,
            "error_code": job.error_code,
            "error_message": job.error_message,
            "model": job.model,
            "recipient": "api.deepseek.com",
            "tokens": job.total_tokens,
            "call_count": len(calls),
            "request_trace_id": job.request_trace_id,
            "sample": entry,
            "provider_requests_real": True,
            "broker_dispatch": "in_process_worker",
            "human_review_required": True,
        }
        if args.phase == "drawing":
            run = (
                db.query(DrawingParseRun)
                .filter(DrawingParseRun.extraction_job_id == job_id)
                .first()
            )
            if run:
                report.update(
                    output=run.output_snapshot,
                    risks=run.risks,
                    persisted={
                        name: db.query(model)
                        .filter(model.revision_id == entry["revision_id"])
                        .count()
                        for name, model in [
                            ("parts", Part),
                            ("joints", WeldJoint),
                            ("requirements", WeldRequirement),
                        ]
                    },
                )
        else:
            entity = (
                db.query(ExtractedEntity)
                .filter(ExtractedEntity.job_id == job_id)
                .first()
            )
            report["ocr_pages"] = [
                {
                    "page": p.page_number,
                    "status": p.ocr_status,
                    "text_chars": len(p.text_content or ""),
                }
                for p in db.query(DocumentPage)
                .filter(DocumentPage.document_id == entry["document_id"])
                .order_by(DocumentPage.page_number)
                .all()
            ]
            if entity:
                report["fields"] = [
                    {
                        "key": f.field_key,
                        "value": f.normalized_value,
                        "confidence": f.confidence,
                        "evidence_count": db.query(FieldEvidence)
                        .filter(FieldEvidence.extracted_field_id == f.id)
                        .count(),
                    }
                    for f in db.query(ExtractedField)
                    .filter(ExtractedField.entity_id == entity.id)
                    .all()
                ]
        write_json(args.output / f"{args.phase}-{job_id}.json", report)
        print(
            json.dumps(
                {
                    k: report[k]
                    for k in [
                        "job_id",
                        "phase",
                        "status",
                        "error_code",
                        "error_message",
                        "model",
                        "tokens",
                        "call_count",
                    ]
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    local.dispose()
    admin.dispose()
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
