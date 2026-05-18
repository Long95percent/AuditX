import { useEffect, useState } from "react";

import { createAuditJob, getHealthStatus, type HealthStatus } from "../api/auditJobs";
import type { AuditJob } from "../types/audit";

const DEMO_FILE_PATH = "demo_resume.pdf";

function formatBBox(bbox: { x0: number; y0: number; x1: number; y1: number }) {
  return `x0=${bbox.x0}, y0=${bbox.y0}, x1=${bbox.x1}, y1=${bbox.y1}`;
}

export function App() {
  const [job, setJob] = useState<AuditJob | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshHealth() {
    setIsCheckingHealth(true);
    try {
      const nextHealth = await getHealthStatus();
      setHealth(nextHealth);
      setError(null);
    } catch (healthError) {
      setHealth(null);
      setError(
        healthError instanceof Error
          ? `Backend health check failed: ${healthError.message}`
          : "Backend health check failed with an unknown error",
      );
    } finally {
      setIsCheckingHealth(false);
    }
  }

  useEffect(() => {
    void refreshHealth();
  }, []);

  async function handleRunAudit() {
    setIsRunning(true);
    setError(null);

    try {
      const nextHealth = await getHealthStatus();
      setHealth(nextHealth);
      const nextJob = await createAuditJob(DEMO_FILE_PATH);
      setJob(nextJob);
    } catch (auditError) {
      setError(auditError instanceof Error ? auditError.message : "Unknown audit error");
    } finally {
      setIsRunning(false);
    }
  }

  const findings = job?.findings ?? [];
  const backendStatus = health ? `${health.status} (${health.env})` : "offline";

  return (
    <main className="app-shell">
      <section className="glass-panel hero-panel">
        <p className="eyebrow">AuditX / VeriDoc</p>
        <h1>Industrial Desktop Document Audit</h1>
        <p className="hero-copy">
          Evidence-first audit workspace for document preview, bbox-level findings,
          and Tauri sidecar orchestration.
        </p>
        <div className="audit-action-row">
          <button className="primary-button" disabled={isRunning} onClick={handleRunAudit}>
            {isRunning ? "Running Fake Audit..." : "Run Fake Audit"}
          </button>
          <button className="secondary-button" disabled={isCheckingHealth} onClick={refreshHealth}>
            {isCheckingHealth ? "Checking Backend..." : "Check Backend"}
          </button>
          <span className={`status-pill ${health ? "status-online" : "status-offline"}`}>
            Backend: {backendStatus}
          </span>
          <span className="status-pill">Audit: {job?.status ?? "not started"}</span>
        </div>
        {error ? <div className="error-panel">{error}</div> : null}
      </section>

      <section className="workspace-grid">
        <div className="glass-panel document-panel">
          <p className="panel-label">Document</p>
          <h2>{job?.file_path ?? DEMO_FILE_PATH}</h2>
          <p>Document ID: {job?.document_id ?? "waiting for audit"}</p>
          <p>Rejected candidates: {job?.rejected_count ?? 0}</p>
        </div>

        <div className="glass-panel findings-panel">
          <p className="panel-label">Findings</p>
          <h2>{findings.length}</h2>
          <div className="findings-list">
            {findings.length === 0 ? (
              <p className="muted-copy">No findings yet. Start the fake audit to load results.</p>
            ) : (
              findings.map((finding) => (
                <article className="finding-card" key={finding.finding_id}>
                  <div className="finding-card-header">
                    <h3>{finding.title}</h3>
                    <span className={`risk-badge risk-${finding.risk_level}`}>
                      {finding.risk_level}
                    </span>
                  </div>
                  <p>{finding.description}</p>
                  <div className="finding-meta">
                    <span>Rule: {finding.rule_id}</span>
                    <span>Confidence: {Math.round(finding.confidence * 100)}%</span>
                    <span>Agent: {finding.source_agent}</span>
                  </div>
                  {finding.evidences.map((evidence) => (
                    <div className="evidence-box" key={`${finding.finding_id}-${evidence.block_id}`}>
                      <strong>Evidence quote:</strong> {evidence.quote}
                      <br />
                      <strong>Page:</strong> {evidence.page_number} · <strong>Block:</strong>{" "}
                      {evidence.block_id}
                      <br />
                      <strong>BBox:</strong> {formatBBox(evidence.bbox)}
                    </div>
                  ))}
                  <p className="suggestion-copy">Suggestion: {finding.suggestion}</p>
                </article>
              ))
            )}
          </div>
        </div>

        <div className="glass-panel timeline-panel">
          <p className="panel-label">Audit Timeline</p>
          <ol className="timeline-list">
            <li>Desktop shell loaded on Vite dev server.</li>
            <li>Backend health is checked before audit execution.</li>
            <li>Fake audit request posts to FastAPI at 127.0.0.1:8765.</li>
            <li>Evidence validator accepts findings with traceable bbox evidence.</li>
          </ol>
        </div>
      </section>
    </main>
  );
}
