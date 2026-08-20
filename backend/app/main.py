"""
Main application entry point for the welding system backend.
"""
import logging
import os

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.health import assert_ready_or_raise, liveness, readiness
from app.core.observability import RequestContextMiddleware, configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)


if not settings.DEVELOPMENT:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "sdhaohan.cn",
            "*.sdhaohan.cn",
            "api.sdhaohan.cn",
            "laimiu.sdhaohan.cn",
            "localhost",
            "127.0.0.1",
        ],
    )

if settings.DEVELOPMENT:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.ALLOWED_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Hanxu Backend")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    if settings.DEVELOPMENT:
        logger.warning(
            "Skipping implicit create_all(); run `alembic upgrade head` for schema changes"
        )
        try:
            from sqlalchemy import text
            from app.core.database import SessionLocal
            from app.services.subscription_plan_seed import ensure_subscription_plans

            db = SessionLocal()
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences TEXT"))
                db.execute(
                    text(
                        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS inspection_type VARCHAR(50)"
                    )
                )
                db.execute(
                    text(
                        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS inspector_name VARCHAR(100)"
                    )
                )
                db.execute(
                    text(
                        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS project_name VARCHAR(200)"
                    )
                )
                db.execute(
                    text(
                        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS vessel_no VARCHAR(100)"
                    )
                )
                db.execute(
                    text(
                        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS work_order_no VARCHAR(100)"
                    )
                )
                db.execute(
                    text(
                        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS weld_joint_number VARCHAR(100)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_quality_inspections_vessel_no "
                        "ON quality_inspections (vessel_no)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_quality_inspections_work_order_no "
                        "ON quality_inspections (work_order_no)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_quality_inspections_weld_joint_number "
                        "ON quality_inspections (weld_joint_number)"
                    )
                )
                db.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS welder_certified_projects (
                            id SERIAL PRIMARY KEY,
                            certification_id INTEGER NOT NULL REFERENCES welder_certifications(id) ON DELETE CASCADE,
                            welder_id INTEGER NOT NULL REFERENCES welders(id) ON DELETE CASCADE,
                            project_code VARCHAR(100),
                            project_name VARCHAR(200) NOT NULL,
                            issue_date DATE,
                            expiry_date DATE,
                            renewal_date DATE,
                            renewal_count INTEGER DEFAULT 0,
                            next_renewal_date DATE,
                            renewal_result VARCHAR(50),
                            renewal_notes TEXT,
                            status VARCHAR(50) DEFAULT 'valid',
                            is_active BOOLEAN DEFAULT TRUE,
                            notes TEXT,
                            created_by INTEGER NOT NULL REFERENCES users(id),
                            updated_by INTEGER REFERENCES users(id),
                            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_welder_certified_projects_certification_id "
                        "ON welder_certified_projects (certification_id)"
                    )
                )
                db.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_welder_certified_projects_welder_id "
                        "ON welder_certified_projects (welder_id)"
                    )
                )
                db.commit()
                created = ensure_subscription_plans(db)
                if created:
                    logger.info("Initialized %s subscription plans for empty database", created)
            finally:
                db.close()
        except Exception as exc:
            logger.warning("Failed to ensure schema patches / subscription plans: %s", exc)
    else:
        assert_ready_or_raise()
    logger.info("Hanxu Backend started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Hanxu Backend")


@app.get("/health")
def liveness_probe():
    """Process liveness. Does not check PostgreSQL or Redis."""
    return liveness()


@app.get("/ready")
@app.get("/api/v1/health")
def readiness_probe():
    """Readiness: PostgreSQL + Redis. Used by Compose/Docker HEALTHCHECK."""
    report = readiness()
    status_code = (
        status.HTTP_200_OK
        if report["status"] == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=status_code, content=report)


@app.get("/")
def root():
    return {
        "message": "Welcome to Hanxu Backend API",
        "version": settings.APP_VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "api_url": settings.API_V1_STR,
    }


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEVELOPMENT,
        log_level=settings.LOG_LEVEL.lower(),
    )
