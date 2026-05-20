import { API_BASE_URL } from "../config";
import type { ParsedDocument } from "../types/audit";
import type {
  BatchCandidate,
  BatchRecord,
  CandidateDetail,
  CandidateListItem,
  EvidenceIndexRecord,
  ResumeRecord,
  ResumeStatus,
} from "../types/resumeLibrary";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`AuditX batch API request failed: ${response.status} ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function listResumes(status?: ResumeStatus): Promise<ResumeRecord[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const payload = await requestJson<{ resumes: ResumeRecord[] }>(`/api/resumes${query}`);
  return payload.resumes;
}

export async function listCandidates(): Promise<CandidateListItem[]> {
  const payload = await requestJson<{ candidates: CandidateListItem[] }>("/api/candidates");
  return payload.candidates;
}

export async function queryCandidates(params: {
  layer?: string;
  minScore?: number;
  maxRiskCount?: number;
}): Promise<CandidateListItem[]> {
  const query = new URLSearchParams();
  if (params.layer) {
    query.set("layer", params.layer);
  }
  if (params.minScore !== undefined) {
    query.set("min_score", String(params.minScore));
  }
  if (params.maxRiskCount !== undefined) {
    query.set("max_risk_count", String(params.maxRiskCount));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const payload = await requestJson<{ candidates: CandidateListItem[] }>(`/api/candidates${suffix}`);
  return payload.candidates;
}

export async function getCandidate(candidateId: string): Promise<CandidateDetail> {
  return requestJson<CandidateDetail>(`/api/candidates/${candidateId}`);
}

export async function getCandidateEvidence(candidateId: string): Promise<EvidenceIndexRecord[]> {
  const payload = await requestJson<{ evidence: EvidenceIndexRecord[] }>(
    `/api/candidates/${candidateId}/evidence`,
  );
  return payload.evidence;
}

export function getCandidateDocumentUrl(candidateId: string): string {
  return `${API_BASE_URL}/api/candidates/${candidateId}/document`;
}

export async function getCandidateParsedDocument(candidateId: string): Promise<ParsedDocument> {
  return requestJson<ParsedDocument>(`/api/candidates/${candidateId}/parsed-document`);
}

export async function createBatch(name: string): Promise<BatchRecord> {
  return requestJson<BatchRecord>("/api/batches", {
    method: "POST",
    body: JSON.stringify({
      batch_id: `batch_${Date.now()}`,
      name,
      job_template_id: "frontend_engineer",
      created_at: new Date().toISOString(),
    }),
  });
}

export async function listBatches(): Promise<BatchRecord[]> {
  const payload = await requestJson<{ batches: BatchRecord[] }>("/api/batches");
  return payload.batches;
}

export async function addBatchCandidate(
  batchId: string,
  candidateId: string,
): Promise<BatchCandidate> {
  return requestJson<BatchCandidate>(`/api/batches/${batchId}/candidates`, {
    method: "POST",
    body: JSON.stringify({ candidate_id: candidateId, created_at: new Date().toISOString() }),
  });
}

export async function importBatchFiles(
  batchId: string,
  filePaths: string[],
): Promise<BatchCandidate[]> {
  const payload = await requestJson<{ candidates: BatchCandidate[] }>(
    `/api/batches/${batchId}/import-files`,
    {
      method: "POST",
      body: JSON.stringify({ file_paths: filePaths, imported_at: new Date().toISOString() }),
    },
  );
  return payload.candidates;
}

export async function runBatch(batchId: string): Promise<BatchCandidate[]> {
  const payload = await requestJson<{ candidates: BatchCandidate[] }>(`/api/batches/${batchId}/run`, {
    method: "POST",
    body: JSON.stringify({ updated_at: new Date().toISOString() }),
  });
  return payload.candidates;
}

export async function retryFailedBatchCandidates(batchId: string): Promise<BatchCandidate[]> {
  const payload = await requestJson<{ candidates: BatchCandidate[] }>(
    `/api/batches/${batchId}/retry-failed`,
    {
      method: "POST",
      body: JSON.stringify({ updated_at: new Date().toISOString() }),
    },
  );
  return payload.candidates;
}

export async function getBatch(batchId: string): Promise<{
  batch: BatchRecord;
  candidates: BatchCandidate[];
}> {
  return requestJson<{ batch: BatchRecord; candidates: BatchCandidate[] }>(`/api/batches/${batchId}`);
}

export async function rerankBatch(
  batchId: string,
  topN: number,
): Promise<{ batch: BatchRecord; candidates: BatchCandidate[] }> {
  return requestJson<{ batch: BatchRecord; candidates: BatchCandidate[] }>(
    `/api/batches/${batchId}/rerank`,
    {
      method: "POST",
      body: JSON.stringify({ top_n: topN, updated_at: new Date().toISOString() }),
    },
  );
}

export async function getBatchTopN(batchId: string, limit: number): Promise<BatchCandidate[]> {
  const payload = await requestJson<{ candidates: BatchCandidate[] }>(
    `/api/batches/${batchId}/top-n?limit=${encodeURIComponent(limit)}`,
  );
  return payload.candidates;
}
