import { open } from "@tauri-apps/plugin-dialog";
import { useEffect, useState } from "react";

import {
  addBatchCandidate,
  createBatch,
  getBatch,
  getCandidate,
  getCandidateDocumentUrl,
  getCandidateEvidence,
  getCandidateParsedDocument,
  getBatchTopN,
  importBatchFiles,
  listBatches,
  listCandidates,
  listResumes,
  queryCandidates,
  rerankBatch,
  retryFailedBatchCandidates,
  runBatch,
} from "../api/resumeLibrary";
import type { Evidence } from "../types/audit";
import type {
  BatchCandidate,
  BatchRecord,
  CandidateDetail,
  CandidateListItem,
  EvidenceIndexRecord,
  ResumeRecord,
} from "../types/resumeLibrary";
import { PdfEvidenceViewer } from "./PdfEvidenceViewer";

export function BatchScreeningWorkspace() {
  const [resumes, setResumes] = useState<ResumeRecord[]>([]);
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [candidateDetail, setCandidateDetail] = useState<CandidateDetail | null>(null);
  const [candidateEvidence, setCandidateEvidence] = useState<EvidenceIndexRecord[]>([]);
  const [selectedPdfEvidence, setSelectedPdfEvidence] = useState<Evidence | null>(null);
  const [batches, setBatches] = useState<BatchRecord[]>([]);
  const [batch, setBatch] = useState<BatchRecord | null>(null);
  const [batchCandidates, setBatchCandidates] = useState<BatchCandidate[]>([]);
  const [topCandidates, setTopCandidates] = useState<BatchCandidate[]>([]);
  const [layerFilter, setLayerFilter] = useState("");
  const [minScoreFilter, setMinScoreFilter] = useState("");
  const [maxRiskFilter, setMaxRiskFilter] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void refreshWorkspace();
  }, []);

  async function refreshWorkspace() {
    setIsLoading(true);
    setError(null);
    try {
      const [nextResumes, nextCandidates, nextBatches] = await Promise.all([
        listResumes(),
        listCandidates(),
        listBatches(),
      ]);
      setResumes(nextResumes);
      setCandidates(nextCandidates);
      setBatches(nextBatches);
      if (selectedCandidateId) {
        await loadCandidate(selectedCandidateId);
      }
    } catch (workspaceError) {
      setError(workspaceError instanceof Error ? workspaceError.message : "Unable to load workspace");
    } finally {
      setIsLoading(false);
    }
  }

  async function applyCandidateFilters() {
    setError(null);
    try {
      const nextCandidates = await queryCandidates({
        layer: layerFilter || undefined,
        minScore: minScoreFilter ? Number(minScoreFilter) : undefined,
        maxRiskCount: maxRiskFilter ? Number(maxRiskFilter) : undefined,
      });
      setCandidates(nextCandidates);
    } catch (filterError) {
      setError(filterError instanceof Error ? filterError.message : "Unable to apply filters");
    }
  }

  async function loadBatch(batchId: string) {
    setError(null);
    try {
      const detail = await getBatch(batchId);
      const nextTopCandidates = await getBatchTopN(batchId, 10);
      setBatch(detail.batch);
      setBatchCandidates(detail.candidates);
      setTopCandidates(nextTopCandidates);
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to load batch");
    }
  }

  async function loadCandidate(candidateId: string) {
    setSelectedCandidateId(candidateId);
    setError(null);
    try {
      const [detail, evidence] = await Promise.all([
        getCandidate(candidateId),
        getCandidateEvidence(candidateId),
      ]);
      setCandidateDetail(detail);
      setCandidateEvidence(evidence);
      setSelectedPdfEvidence(toPdfEvidence(evidence[0]));
    } catch (candidateError) {
      setError(candidateError instanceof Error ? candidateError.message : "Unable to load candidate");
    }
  }

  function selectEvidence(evidence: EvidenceIndexRecord) {
    setSelectedPdfEvidence(toPdfEvidence(evidence));
  }

  function toPdfEvidence(evidence: EvidenceIndexRecord | undefined): Evidence | null {
    if (!evidence?.bbox) {
      return null;
    }
    return {
      document_id: evidence.resume_id,
      page_number: evidence.page_number,
      block_id: evidence.block_id,
      quote: evidence.text_excerpt,
      bbox: evidence.bbox,
    };
  }

  async function handleCreateBatch() {
    setError(null);
    try {
      const nextBatch = await createBatch("Frontend Screening Batch");
      setBatch(nextBatch);
      setBatchCandidates([]);
      setTopCandidates([]);
      setBatches((current) => [nextBatch, ...current]);
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to create batch");
    }
  }

  async function handleAddCandidate(candidateId: string) {
    if (!batch) {
      setError("Create a batch before adding candidates.");
      return;
    }
    setError(null);
    try {
      await addBatchCandidate(batch.batch_id, candidateId);
      const detail = await getBatch(batch.batch_id);
      setBatch(detail.batch);
      setBatchCandidates(detail.candidates);
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to add candidate");
    }
  }

  async function handleImportFiles() {
    if (!batch) {
      setError("Create or select a batch before importing files.");
      return;
    }
    setError(null);
    try {
      const selected = await open({
        multiple: true,
        directory: false,
        filters: [{ name: "Documents", extensions: ["pdf", "doc", "docx", "txt"] }],
      });
      const filePaths = Array.isArray(selected) ? selected.filter((item): item is string => typeof item === "string") : [];
      if (!filePaths.length) {
        return;
      }
      await importBatchFiles(batch.batch_id, filePaths);
      await loadBatch(batch.batch_id);
      await refreshWorkspace();
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to import files");
    }
  }

  async function handleRunBatch() {
    if (!batch) {
      setError("Create or select a batch before running review.");
      return;
    }
    setError(null);
    try {
      const candidates = await runBatch(batch.batch_id);
      setBatchCandidates(candidates);
      await refreshWorkspace();
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to run batch");
    }
  }

  async function handleRetryFailed() {
    if (!batch) {
      setError("Create or select a batch before retrying failures.");
      return;
    }
    setError(null);
    try {
      const candidates = await retryFailedBatchCandidates(batch.batch_id);
      setBatchCandidates(candidates);
      await loadBatch(batch.batch_id);
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to retry failed candidates");
    }
  }

  async function handleRerankBatch() {
    if (!batch) {
      setError("Create a batch before reranking candidates.");
      return;
    }
    setError(null);
    try {
      const detail = await rerankBatch(batch.batch_id, 10);
      const nextTopCandidates = await getBatchTopN(batch.batch_id, 10);
      setBatch(detail.batch);
      setBatchCandidates(detail.candidates);
      setTopCandidates(nextTopCandidates);
    } catch (batchError) {
      setError(batchError instanceof Error ? batchError.message : "Unable to rerank batch");
    }
  }

  return (
    <section className="batch-workspace">
      <div className="workspace-toolbar glass-panel">
        <div>
          <p className="panel-label">Batch Screening Workspace</p>
          <h2>简历库、候选人表格与批次骨架</h2>
          <p className="muted-copy">
            当前展示真实 API / SQLite 数据。并发 worker、自动批量运行、压测证明尚未接入。
          </p>
        </div>
        <div className="audit-action-row compact-actions">
          <button className="secondary-button" onClick={refreshWorkspace} disabled={isLoading}>
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
          <button className="primary-button" onClick={handleCreateBatch}>Create Draft Batch</button>
          <button className="secondary-button" onClick={handleImportFiles}>Import Files</button>
          <button className="secondary-button" onClick={handleRunBatch}>Run Pending</button>
          <button className="secondary-button" onClick={handleRetryFailed}>Retry Failed</button>
        </div>
      </div>

      {error ? <div className="error-panel">{error}</div> : null}

      <div className="batch-grid">
        <section className="glass-panel batch-panel">
          <div className="section-heading-row">
            <h3>Resume Library</h3>
            <span className="status-pill">{resumes.length} resumes</span>
          </div>
          {resumes.length ? (
            <div className="compact-list">
              {resumes.map((resume) => (
                <article key={resume.resume_id} className="compact-card">
                  <strong>{resume.filename}</strong>
                  <span>{resume.status}</span>
                  <small>{resume.parsed_document_id ?? "no parsed artifact"}</small>
                </article>
              ))}
            </div>
          ) : (
            <p className="muted-copy">单份审查完成后会自动沉淀到这里。</p>
          )}
        </section>

        <section className="glass-panel batch-panel candidate-table-panel">
          <div className="section-heading-row">
            <h3>Candidates</h3>
            <span className="status-pill">{candidates.length} candidates</span>
          </div>
          {candidates.length ? (
            <>
            <div className="filter-bar">
              <select value={layerFilter} onChange={(event) => setLayerFilter(event.target.value)}>
                <option value="">All layers</option>
                <option value="best">Best</option>
                <option value="potential">Potential</option>
                <option value="not_recommended">Not recommended</option>
              </select>
              <input
                value={minScoreFilter}
                placeholder="Min score"
                type="number"
                min="0"
                max="100"
                onChange={(event) => setMinScoreFilter(event.target.value)}
              />
              <input
                value={maxRiskFilter}
                placeholder="Max risks"
                type="number"
                min="0"
                onChange={(event) => setMaxRiskFilter(event.target.value)}
              />
              <button className="secondary-button small-button" onClick={applyCandidateFilters}>
                Apply
              </button>
            </div>
            <div className="candidate-table" role="table" aria-label="候选人列表">
              <div className="candidate-table-row candidate-table-head" role="row">
                <span>Name</span>
                <span>Layer</span>
                <span>Score</span>
                <span>Risk</span>
                <span>Actions</span>
              </div>
              {candidates.map((item) => (
                <div className="candidate-table-row" role="row" key={item.profile.candidate_id}>
                  <span>{item.profile.display_name}</span>
                  <span>{item.latest_score?.layer ?? "unscored"}</span>
                  <span>{item.latest_score?.total_score ?? "-"}</span>
                  <span>{item.latest_score?.risk_count ?? "-"}</span>
                  <span className="table-actions">
                    <button className="secondary-button small-button" onClick={() => void loadCandidate(item.profile.candidate_id)}>
                      Detail
                    </button>
                    <button className="secondary-button small-button" onClick={() => void handleAddCandidate(item.profile.candidate_id)}>
                      Add
                    </button>
                  </span>
                </div>
              ))}
            </div>
            </>
          ) : (
            <p className="muted-copy">还没有候选人画像。请先运行单份审查。</p>
          )}
        </section>

        <section className="glass-panel batch-panel">
          <div className="section-heading-row">
            <h3>Candidate Detail</h3>
            <span className="status-pill">{selectedCandidateId ?? "none"}</span>
          </div>
          {candidateDetail ? (
            <div className="detail-stack">
              <strong>{candidateDetail.profile.display_name}</strong>
              <p>{candidateDetail.profile.summary ?? "No summary yet."}</p>
              <p>Scores: {candidateDetail.scores.length} · Findings: {candidateDetail.findings.length}</p>
              <div className="compact-list">
                {candidateEvidence.map((evidence) => (
                  <article className="compact-card" key={evidence.evidence_id}>
                    <strong>{evidence.text_excerpt}</strong>
                    <span>page {evidence.page_number} · block {evidence.block_id}</span>
                    <small>{evidence.parsed_document_artifact_uri}</small>
                    <button className="secondary-button small-button" onClick={() => selectEvidence(evidence)}>
                      Highlight PDF
                    </button>
                  </article>
                ))}
              </div>
              {candidateDetail.profile.review_session_id && selectedPdfEvidence ? (
                <PdfEvidenceViewer
                  selectedEvidence={selectedPdfEvidence}
                  documentUrl={getCandidateDocumentUrl(candidateDetail.profile.candidate_id)}
                  loadParsedDocument={() => getCandidateParsedDocument(candidateDetail.profile.candidate_id)}
                />
              ) : (
                <p className="muted-copy">该候选人暂无可高亮 PDF artifact。</p>
              )}
            </div>
          ) : (
            <p className="muted-copy">选择候选人后显示评分、finding 和 evidence index。</p>
          )}
        </section>

        <section className="glass-panel batch-panel">
          <div className="section-heading-row">
            <h3>Draft Batch</h3>
            <span className="status-pill">{batch?.status ?? "not created"}</span>
          </div>
          {batch ? (
            <div className="detail-stack">
              {batches.length ? (
                <select value={batch.batch_id} onChange={(event) => void loadBatch(event.target.value)}>
                  {batches.map((item) => (
                    <option value={item.batch_id} key={item.batch_id}>{item.name} · {item.status}</option>
                  ))}
                </select>
              ) : null}
              <strong>{batch.name}</strong>
              <p>Template: {batch.job_template_id}</p>
              <p>Candidates: {batchCandidates.length}</p>
              <button className="primary-button" onClick={handleRerankBatch}>
                Rerank Top 10
              </button>
              <div className="compact-list">
                {batchCandidates.map((candidate) => (
                  <article className="compact-card" key={candidate.candidate_id}>
                    <strong>{candidate.rank ? `#${candidate.rank} ` : ""}{candidate.candidate_id}</strong>
                    <span>{candidate.status} · score {candidate.score_id ?? "unscored"}</span>
                    <small>{candidate.included_reason ?? candidate.eliminated_reason ?? candidate.error ?? "no reason yet"}</small>
                  </article>
                ))}
              </div>
              {topCandidates.length ? (
                <div className="top-n-panel">
                  <strong>Current Top N</strong>
                  {topCandidates.map((candidate) => (
                    <span key={candidate.candidate_id}>
                      #{candidate.rank} {candidate.candidate_id} · {candidate.included_reason}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="detail-stack">
              {batches.length ? (
                <select defaultValue="" onChange={(event) => void loadBatch(event.target.value)}>
                  <option value="" disabled>Select existing batch</option>
                  {batches.map((item) => (
                    <option value={item.batch_id} key={item.batch_id}>{item.name} · {item.status}</option>
                  ))}
                </select>
              ) : null}
              <p className="muted-copy">创建草稿批次后，可把候选人加入批次；尚不自动运行排序。</p>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}
