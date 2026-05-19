from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auditx.api.routes_audit_jobs import router as audit_jobs_router
from auditx.api.routes_job_templates import router as job_templates_router
from auditx.api.routes_settings import router as settings_router
from auditx.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AuditX / VeriDoc API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:1420", "http://localhost:1420"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.include_router(audit_jobs_router)
    app.include_router(settings_router)
    app.include_router(job_templates_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.env}

    return app


app = create_app()


