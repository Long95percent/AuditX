import hashlib
import json
from pathlib import Path
from typing import Any

from auditx.domain.artifacts import ArtifactRef


class FileSystemArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_bytes(
        self,
        owner_type: str,
        owner_id: str,
        artifact_type: str,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> ArtifactRef:
        owner_dir = self._owner_dir(owner_type, owner_id)
        owner_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = Path(filename).name
        path = owner_dir / safe_filename
        path.write_bytes(content)
        relative_path = path.relative_to(self.root).as_posix()
        return ArtifactRef(
            artifact_uri=f"local://artifacts/{relative_path}",
            artifact_type=artifact_type,
            content_type=content_type,
            sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
        )

    def resolve(self, artifact: ArtifactRef) -> Path:
        prefix = "local://artifacts/"
        if not artifact.artifact_uri.startswith(prefix):
            raise ValueError("unsupported artifact uri")
        path = (self.root / artifact.artifact_uri.removeprefix(prefix)).resolve()
        root = self.root.resolve()
        path.relative_to(root)
        return path

    def write_json(
        self,
        owner_type: str,
        owner_id: str,
        artifact_type: str,
        filename: str,
        payload: Any,
    ) -> ArtifactRef:
        content = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        return self.write_bytes(
            owner_type=owner_type,
            owner_id=owner_id,
            artifact_type=artifact_type,
            filename=filename,
            content=content,
            content_type="application/json",
        )

    def _owner_dir(self, owner_type: str, owner_id: str) -> Path:
        if owner_type == "job":
            return self.root / "jobs" / owner_id
        if owner_type == "resume":
            return self.root / "resumes" / owner_id
        return self.root / owner_type / owner_id
