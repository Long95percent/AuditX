from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auditx.api.dependencies import get_batch_review_service
from auditx.application.batch_review_service import BatchReviewService
from auditx.domain.batch import BatchCandidate, BatchRecord

router = APIRouter(prefix="/api/batches", tags=["batches"])


class CreateBatchRequest(BaseModel):
    batch_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    job_template_id: str = Field(min_length=1)
    created_at: datetime


class AddBatchCandidateRequest(BaseModel):
    candidate_id: str = Field(min_length=1)
    created_at: datetime


class ImportBatchFilesRequest(BaseModel):
    file_paths: list[str] = Field(min_length=1)
    imported_at: datetime


class FailBatchCandidateRequest(BaseModel):
    error: str = Field(min_length=1)
    updated_at: datetime


class RerankBatchRequest(BaseModel):
    top_n: int = Field(gt=0)
    updated_at: datetime


class BatchRunRequest(BaseModel):
    updated_at: datetime


class BatchDetailResponse(BaseModel):
    batch: BatchRecord
    candidates: list[BatchCandidate]


class BatchCandidatesResponse(BaseModel):
    candidates: list[BatchCandidate]


class BatchListResponse(BaseModel):
    batches: list[BatchRecord]


@router.post("", response_model=BatchRecord)
def create_batch(
    request: CreateBatchRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchRecord:
    return service.create_batch(
        batch_id=request.batch_id,
        name=request.name,
        job_template_id=request.job_template_id,
        created_at=request.created_at,
    )


@router.get("", response_model=BatchListResponse)
def list_batches(
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchListResponse:
    return BatchListResponse(batches=service.list_batches())


@router.post("/{batch_id}/candidates", response_model=BatchCandidate)
def add_candidate(
    batch_id: str,
    request: AddBatchCandidateRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchCandidate:
    return service.add_candidate(
        batch_id=batch_id,
        candidate_id=request.candidate_id,
        created_at=request.created_at,
    )


@router.post("/{batch_id}/import-files", response_model=BatchCandidatesResponse)
def import_batch_files(
    batch_id: str,
    request: ImportBatchFilesRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchCandidatesResponse:
    if service.get_batch(batch_id) is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchCandidatesResponse(
        candidates=service.import_files(
            batch_id=batch_id,
            file_paths=request.file_paths,
            imported_at=request.imported_at,
        )
    )


@router.post("/{batch_id}/candidates/{candidate_id}/fail", response_model=BatchCandidate)
def mark_candidate_failed(
    batch_id: str,
    candidate_id: str,
    request: FailBatchCandidateRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchCandidate:
    return service.mark_candidate_failed(
        batch_id=batch_id,
        candidate_id=candidate_id,
        error=request.error,
        updated_at=request.updated_at,
    )


@router.post("/{batch_id}/rerank", response_model=BatchDetailResponse)
def rerank_batch(
    batch_id: str,
    request: RerankBatchRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchDetailResponse:
    batch = service.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    candidates = service.rerank(batch_id=batch_id, top_n=request.top_n, updated_at=request.updated_at)
    next_batch = service.get_batch(batch_id)
    if next_batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchDetailResponse(batch=next_batch, candidates=candidates)


@router.post("/{batch_id}/run", response_model=BatchCandidatesResponse)
def run_batch(
    batch_id: str,
    request: BatchRunRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchCandidatesResponse:
    if service.get_batch(batch_id) is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchCandidatesResponse(candidates=service.run_pending(batch_id, request.updated_at))


@router.post("/{batch_id}/retry-failed", response_model=BatchCandidatesResponse)
def retry_failed_batch_candidates(
    batch_id: str,
    request: BatchRunRequest,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchCandidatesResponse:
    if service.get_batch(batch_id) is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchCandidatesResponse(candidates=service.retry_failed(batch_id, request.updated_at))


@router.get("/{batch_id}/top-n", response_model=BatchCandidatesResponse)
def get_batch_top_n(
    batch_id: str,
    limit: int = Query(default=20, gt=0),
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchCandidatesResponse:
    if service.get_batch(batch_id) is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchCandidatesResponse(candidates=service.top_n(batch_id=batch_id, limit=limit))


@router.get("/{batch_id}", response_model=BatchDetailResponse)
def get_batch(
    batch_id: str,
    service: BatchReviewService = Depends(get_batch_review_service),
) -> BatchDetailResponse:
    batch = service.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchDetailResponse(
        batch=batch,
        candidates=service.list_candidates(batch_id),
    )
