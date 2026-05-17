from fastapi import FastAPI

from auditx.api.routes_audit_jobs import router as audit_jobs_router
from auditx.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AuditX / VeriDoc API", version="0.1.0")
    app.include_router(audit_jobs_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.env}

    return app


app = create_app()
