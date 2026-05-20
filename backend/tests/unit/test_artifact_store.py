from pathlib import Path

from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore


def test_file_system_artifact_store_writes_bytes_with_metadata() -> None:
    root = Path("backend/tests/.artifact_tmp")
    store = FileSystemArtifactStore(root)

    artifact = store.write_bytes(
        owner_type="job",
        owner_id="job_123",
        artifact_type="ocr_raw",
        filename="raw.json",
        content=b'{"ok": true}',
        content_type="application/json",
    )

    assert artifact.artifact_uri.startswith("local://artifacts/jobs/job_123/")
    assert artifact.artifact_type == "ocr_raw"
    assert artifact.content_type == "application/json"
    assert artifact.size_bytes == 12
    assert artifact.sha256
    assert store.resolve(artifact).read_bytes() == b'{"ok": true}'
