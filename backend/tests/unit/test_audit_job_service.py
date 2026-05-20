from auditx.application.audit_job_service import AuditJobService, AuditJobStatus


class RecordingUseCase:
    def __init__(self) -> None:
        self.ran_paths: list[str] = []

    def run(self, file_path: str):
        self.ran_paths.append(file_path)
        raise RuntimeError("stop after proving run was invoked")


def test_create_records_pending_job_without_running_use_case() -> None:
    use_case = RecordingUseCase()
    service = AuditJobService(use_case=use_case)  # type: ignore[arg-type]

    job = service.create("resume.pdf")

    assert job.status == AuditJobStatus.pending
    assert service.get(job.job_id) == job
    assert use_case.ran_paths == []


def test_run_executes_existing_job_by_id() -> None:
    use_case = RecordingUseCase()
    service = AuditJobService(use_case=use_case)  # type: ignore[arg-type]
    job = service.create("resume.pdf")

    service.run(job.job_id)

    assert use_case.ran_paths == ["resume.pdf"]
    assert job.status == AuditJobStatus.failed
    assert job.error == "stop after proving run was invoked"