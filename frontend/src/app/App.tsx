import { open } from "@tauri-apps/plugin-dialog";
import { useEffect, useState } from "react";

import { createAuditJob, getHealthStatus, type HealthStatus } from "../api/auditJobs";
import type { AuditJob } from "../types/audit";

function formatBBox(bbox: { x0: number; y0: number; x1: number; y1: number }) {
  return `x0=${bbox.x0}, y0=${bbox.y0}, x1=${bbox.x1}, y1=${bbox.y1}`;
}

function displayFileName(filePath: string | null) {
  if (!filePath) {
    return "No document selected";
  }
  const parts = filePath.split(/[\\/]/);
  return parts[parts.length - 1] || filePath;
}

export function App() {
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [job, setJob] = useState<AuditJob | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [isPickingFile, setIsPickingFile] = useState(false);
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

  async function handleChooseFile() {
    setIsPickingFile(true);
    setError(null);

    try {
      const selected = await open({
        multiple: false,
        directory: false,
        filters: [
          {
            name: "Documents",
            extensions: ["pdf", "doc", "docx", "txt"],
          },
        ],
      });

      if (typeof selected === "string") {
        setSelectedFilePath(selected);
        setJob(null);
      }
    } catch (pickError) {
      setError(pickError instanceof Error ? pickError.message : "Unable to open file picker");
    } finally {
      setIsPickingFile(false);
    }
  }

  async function handleRunAudit() {
    if (!selectedFilePath) {
      setError("Choose a document before running the audit.");
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      const nextHealth = await getHealthStatus();
      setHealth(nextHealth);
      const nextJob = await createAuditJob(selectedFilePath);
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
          <button className="secondary-button" disabled={isPickingFile} onClick={handleChooseFile}>
            {isPickingFile ? "Choosing Document..." : "Choose Document"}
          </button>
          <button className="primary-button" disabled={isRunning || !selectedFilePath} onClick={handleRunAudit}>
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
        <div className="selected-file-panel">
          <span className="selected-file-label">Selected document</span>
          <strong>{displayFileName(selectedFilePath)}</strong>
          {selectedFilePath ? <code>{selectedFilePath}</code> : null}
        </div>
        {error ? <div className="error-panel">{error}</div> : null}
      </section>

      <section className="workspace-grid">
        <div className="glass-panel document-panel">
          <p className="panel-label">Document</p>
          <h2>{job?.file_path ? displayFileName(job.file_path) : displayFileName(selectedFilePath)}</h2>
          <p>Document ID: {job?.document_id ?? "waiting for audit"}</p>
          <p>Rejected candidates: {job?.rejected_count ?? 0}</p>
        </div>

        <div className="glass-panel findings-panel">
          <p className="panel-label">Findings</p>
          <h2>{findings.length}</h2>
          <div className="findings-list">
            {findings.length === 0 ? (
              <p className="muted-copy">No findings yet. Choose a document and start the fake audit.</p>
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
            <li>User chooses a local document through the Tauri native file dialog.</li>
            <li>Backend health is checked before audit execution.</li>
            <li>Fake audit request posts the selected file path to FastAPI at 127.0.0.1:8765.</li>
            <li>Evidence validator accepts findings with traceable bbox evidence.</li>
          </ol>
        </div>
      </section>
    </main>
  );
}
