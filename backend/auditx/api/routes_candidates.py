from pathlib import Path
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from auditx.api.dependencies import get_batch_evidence_repository, get_candidate_query_service
from auditx.application.candidate_query_service import (
    CandidateDetail,
    CandidateListItem,
    CandidateQueryService,
)
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.scoring import CandidateLayer
from auditx.config.settings import Settings, get_settings
from auditx.domain.artifacts import ArtifactRef
from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore
from auditx.infrastructure.storage.evidence_repository import SQLiteEvidenceRepository

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


class CandidateListResponse(BaseModel):
    candidates: list[CandidateListItem]


class CandidateEvidenceResponse(BaseModel):
    evidence: list[EvidenceIndexRecord]


@router.get("", response_model=CandidateListResponse)
def list_candidates(
    layer: CandidateLayer | None = None,
    min_score: float | None = Query(default=None, ge=0, le=100),
    max_risk_count: int | None = Query(default=None, ge=0),
    service: CandidateQueryService = Depends(get_candidate_query_service),
) -> CandidateListResponse:
    return CandidateListResponse(
        candidates=service.list_candidates(
            layer=layer,
            min_score=min_score,
            max_risk_count=max_risk_count,
        )
    )


@router.get("/top-n", response_model=CandidateListResponse)
def top_candidates(
    limit: int = Query(default=20, gt=0),
    service: CandidateQueryService = Depends(get_candidate_query_service),
) -> CandidateListResponse:
    return CandidateListResponse(candidates=service.top_n(limit=limit))


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(
    candidate_id: str,
    service: CandidateQueryService = Depends(get_candidate_query_service),
) -> CandidateDetail:
    candidate = service.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.get("/{candidate_id}/evidence", response_model=CandidateEvidenceResponse)
def get_candidate_evidence(
    candidate_id: str,
    repository: SQLiteEvidenceRepository = Depends(get_batch_evidence_repository),
) -> CandidateEvidenceResponse:
    return CandidateEvidenceResponse(evidence=repository.list_by_candidate(candidate_id))


@router.get("/{candidate_id}/document")
def get_candidate_document(
    candidate_id: str,
    service: CandidateQueryService = Depends(get_candidate_query_service),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    candidate = service.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    artifact_uri = candidate.profile.source_document_artifact_uri
    if artifact_uri is None:
        raise HTTPException(status_code=404, detail="Candidate source document artifact not found")
    artifact = ArtifactRef(
        artifact_uri=artifact_uri,
        artifact_type="source_document",
        content_type="application/pdf",
        sha256="unknown",
        size_bytes=0,
    )
    store = FileSystemArtifactStore(Path(settings.storage_dir) / "artifacts")
    path = store.resolve(artifact)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Candidate source document artifact file not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.get("/{candidate_id}/parsed-document")
def get_candidate_parsed_document(
    candidate_id: str,
    repository: SQLiteEvidenceRepository = Depends(get_batch_evidence_repository),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    evidence = repository.list_by_candidate(candidate_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Candidate parsed document artifact not found")
    artifact = ArtifactRef(
        artifact_uri=evidence[0].parsed_document_artifact_uri,
        artifact_type="parsed_document",
        content_type="application/json",
        sha256="unknown",
        size_bytes=0,
    )
    store = FileSystemArtifactStore(Path(settings.storage_dir) / "artifacts")
    path = store.resolve(artifact)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Candidate parsed document artifact file not found")
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))
