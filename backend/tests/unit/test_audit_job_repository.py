from pathlib import Path
from uuid import uuid4

from auditx.application.audit_job_service import AuditJob, AuditJobService, AuditJobStatus
from auditx.infrastructure.storage.audit_job_repository import SQLiteAuditJobRepository


class FailingUseCase:
    def run(self, file_path: str):
        raise RuntimeError("repository service persistence check")


def test_sqlite_repository_loads_saved_job_from_new_instance() -> None:
    database_path = _database_path()
    repository = SQLiteAuditJobRepository(database_path)
    job = AuditJob(job_id="job_1", file_path="resume.pdf", status=AuditJobStatus.running)

    repository.save(job)
    loaded = SQLiteAuditJobRepository(database_path).get("job_1")

    assert loaded == job


def test_audit_job_service_reads_jobs_persisted_by_previous_service() -> None:
    database_path = _database_path()
    first_service = AuditJobService(
        use_case=FailingUseCase(),  # type: ignore[arg-type]
        repository=SQLiteAuditJobRepository(database_path),
    )
    job = first_service.create("resume.pdf")
    first_service.run(job.job_id)

    second_service = AuditJobService(
        use_case=FailingUseCase(),  # type: ignore[arg-type]
        repository=SQLiteAuditJobRepository(database_path),
    )
    loaded = second_service.get(job.job_id)

    assert loaded is not None
    assert loaded.status == AuditJobStatus.failed
    assert loaded.error == "repository service persistence check"


def _database_path() -> Path:
    directory = Path("backend/tests/.repo_tmp")
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"audit_jobs_{uuid4().hex}.sqlite3"