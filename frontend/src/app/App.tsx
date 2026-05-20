import { open } from "@tauri-apps/plugin-dialog";
import { useEffect, useState } from "react";

import {
  createAuditJob,
  createJobTemplateFromJD,
  getAuditJob,
  getHealthStatus,
  saveOpenAISettings,
  testOpenAISettings,
  type HealthStatus,
  type OpenAISettingsStatus,
} from "../api/auditJobs";
import type { AuditJob, JobTemplate } from "../types/audit";

function formatBBox(bbox: { x0: number; y0: number; x1: number; y1: number }) {
  return `x0=${bbox.x0}, y0=${bbox.y0}, x1=${bbox.x1}, y1=${bbox.y1}`;
}

function formatMetadataValue(value: unknown) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

async function waitForTerminalJob(jobId: string) {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    const nextJob = await getAuditJob(jobId);
    if (nextJob.status === "completed" || nextJob.status === "failed") {
      return nextJob;
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  return getAuditJob(jobId);
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
  const [isTestCenterOpen, setIsTestCenterOpen] = useState(false);
  const [activeTestPanel, setActiveTestPanel] = useState<string | null>(null);
  const [openAIKey, setOpenAIKey] = useState("");
  const [openAIModel, setOpenAIModel] = useState("gpt-5.4-mini");
  const [openAIBaseUrl, setOpenAIBaseUrl] = useState("https://api.openai.com/v1");
  const [openAIStatus, setOpenAIStatus] = useState<OpenAISettingsStatus | null>(null);
  const [jobTemplateName, setJobTemplateName] = useState("");
  const [jobTemplateJD, setJobTemplateJD] = useState("");
  const [generatedTemplate, setGeneratedTemplate] = useState<JobTemplate | null>(null);
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
      setJob(await waitForTerminalJob(nextJob.job_id));
    } catch (auditError) {
      setError(auditError instanceof Error ? auditError.message : "Unknown audit error");
    } finally {
      setIsRunning(false);
    }
  }

  async function handleSaveOpenAISettings() {
    try {
      const status = await saveOpenAISettings({
        api_key: openAIKey,
        model: openAIModel,
        base_url: openAIBaseUrl,
      });
      setOpenAIStatus(status);
      setError(null);
    } catch (settingsError) {
      setError(settingsError instanceof Error ? settingsError.message : "Unable to save OpenAI settings");
    }
  }

  async function handleTestOpenAISettings() {
    try {
      const status = await testOpenAISettings();
      setOpenAIStatus(status);
      setError(null);
    } catch (settingsError) {
      setError(settingsError instanceof Error ? settingsError.message : "Unable to test OpenAI settings");
    }
  }

  async function handleCreateJobTemplate() {
    try {
      const template = await createJobTemplateFromJD(jobTemplateName, jobTemplateJD);
      setGeneratedTemplate(template);
      setError(null);
    } catch (templateError) {
      setGeneratedTemplate(null);
      setError(templateError instanceof Error ? templateError.message : "Unable to create job template");
    }
  }

  const findings = job?.findings ?? [];
  const rejectedCandidates = job?.rejected_candidates ?? [];
  const traceSteps = job?.trace.steps ?? [];
  const acceptedTraceCount = traceSteps.filter((step) => step.status === "accepted").length;
  const rejectedTraceCount = traceSteps.filter((step) => step.status === "rejected").length;
  const failedTraceCount = traceSteps.filter((step) => step.status === "failed").length;
  const evidenceCount = findings.reduce((count, finding) => count + finding.evidences.length, 0);
  const backendStatus = health ? `${health.status} (${health.env})` : "offline";

  function openTestPanel(panel: string) {
    setActiveTestPanel(panel);
    setIsTestCenterOpen(false);
  }

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
          <button className="secondary-button" onClick={() => setIsTestCenterOpen(true)}>
            验收 / 测试中心
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
        <div className="glass-panel review-summary-panel">
          <p className="panel-label">HR Review Summary</p>
          {job?.score ? (
            <div className="review-summary-grid">
              <div className="score-hero">
                <span>Match Score</span>
                <strong>{job.score.total_score}</strong>
                <em>{job.score.layer.replace("_", " ")}</em>
              </div>
              <div className="summary-stack">
                <p>Template: {job.score.template_id}@{job.score.template_version}</p>
                <p>Advantages: {job.score.advantage_tags.join(" / ") || "none"}</p>
                <p>Risk count: {job.score.risk_count}</p>
                <p>Evidence anchors: {evidenceCount}</p>
              </div>
              <div className="dimension-grid product-dimensions">
                {Object.entries(job.score.dimension_scores).map(([name, value]) => (
                  <span key={name}>{name}: {value}</span>
                ))}
              </div>
              <ul className="calculation-list">
                {job.score.calculation_details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="muted-copy">Run an audit to see score, layer, advantages, and dimensions.</p>
          )}
        </div>

        <div className="glass-panel document-panel">
          <p className="panel-label">Document</p>
          <h2>{job?.file_path ? displayFileName(job.file_path) : displayFileName(selectedFilePath)}</h2>
          <p>Document ID: {job?.document_id ?? "waiting for audit"}</p>
          <p>Status: {job?.status ?? "not started"}</p>
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
          <p className="panel-label">Agent Trace</p>
          <div className="trace-summary-row">
            <span className="status-pill">Steps: {traceSteps.length}</span>
            <span className="status-pill status-online">Accepted: {acceptedTraceCount}</span>
            <span className="status-pill">Rejected: {rejectedTraceCount}</span>
            <span className={failedTraceCount ? "status-pill status-offline" : "status-pill"}>
              Failed: {failedTraceCount}
            </span>
          </div>
          {traceSteps.length ? (
            <ol className="timeline-list product-trace-list">
              {traceSteps.map((step) => (
                <li className={`trace-row trace-${step.status}`} key={step.step_id}>
                  <div className="trace-row-header">
                    <strong>{step.name}</strong>
                    <span>{step.step_type} · {step.status}</span>
                  </div>
                  {step.input_summary ? <p>Input: {step.input_summary}</p> : null}
                  {step.output_summary ? <p>Output: {step.output_summary}</p> : null}
                  {step.error ? <p className="rejected-copy">Error: {step.error}</p> : null}
                  {Object.keys(step.metadata).length ? (
                    <dl className="metadata-grid">
                      {Object.entries(step.metadata).map(([key, value]) => (
                        <div key={`${step.step_id}-${key}`}>
                          <dt>{key}</dt>
                          <dd>{formatMetadataValue(value)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : null}
                </li>
              ))}
            </ol>
          ) : (
            <ol className="timeline-list">
              <li>Choose a local document through the Tauri native file dialog.</li>
              <li>Run audit to invoke AgentOrchestrator, tools, evidence gate, score, and trace.</li>
              <li>Review formal risks, rejected candidates, evidence, and calculation details here.</li>
            </ol>
          )}
        </div>

        <div className="glass-panel rejected-panel">
          <p className="panel-label">Rejected Candidates</p>
          {rejectedCandidates.length ? (
            <div className="findings-list">
              {rejectedCandidates.map((candidate) => (
                <article className="finding-card" key={`rejected-${candidate.candidate_id}`}>
                  <div className="finding-card-header">
                    <h3>{candidate.title}</h3>
                    <span className={`risk-badge risk-${candidate.risk_level}`}>{candidate.risk_level}</span>
                  </div>
                  <p>{candidate.description}</p>
                  <div className="finding-meta">
                    <span>Candidate: {candidate.candidate_id}</span>
                    <span>Evidence: {candidate.evidences.length}</span>
                    <span>Source: {candidate.source_agent}</span>
                  </div>
                  <p className="rejected-copy">
                    未进入正式风险：{candidate.rejection_reason ?? "missing verified evidence"}
                  </p>
                  {candidate.evidences.map((evidence) => (
                    <div className="evidence-box" key={`${candidate.candidate_id}-${evidence.block_id}`}>
                      <strong>Candidate evidence:</strong> {evidence.quote}
                      <br />
                      <strong>Page:</strong> {evidence.page_number} · <strong>Block:</strong>{" "}
                      {evidence.block_id}
                      <br />
                      <strong>BBox:</strong> {formatBBox(evidence.bbox)}
                    </div>
                  ))}
                </article>
              ))}
            </div>
          ) : (
            <p className="muted-copy">No rejected candidates yet.</p>
          )}
        </div>
      </section>

      {isTestCenterOpen ? (
        <div className="acceptance-backdrop" role="dialog" aria-modal="true" aria-label="验收测试中心">
          <aside className="acceptance-panel glass-panel">
            <div className="acceptance-header">
              <div>
                <p className="panel-label">Test Center</p>
                <h2>验收 / 测试中心</h2>
              </div>
              <button className="secondary-button" onClick={() => setIsTestCenterOpen(false)}>
                关闭
              </button>
            </div>
            <section className="test-category">
              <p className="panel-label">运行类测试</p>
              <button className="test-card" onClick={() => openTestPanel("runtime")}>后端与任务状态</button>
              <button className="test-card" onClick={() => openTestPanel("trace")}>Agent / Tool Trace</button>
            </section>
            <section className="test-category">
              <p className="panel-label">结果类测试</p>
              <button className="test-card" onClick={() => openTestPanel("candidates")}>Candidates / Rejected</button>
              <button className="test-card" onClick={() => openTestPanel("score")}>Score / Layer</button>
              <button className="test-card" onClick={() => openTestPanel("evidence")}>Evidence</button>
            </section>
            <section className="test-category">
              <p className="panel-label">配置类测试</p>
              <button className="test-card" onClick={() => openTestPanel("openai")}>OpenAI 设置 / JD 模板</button>
            </section>
          </aside>
        </div>
      ) : null}

      {activeTestPanel ? (
        <div className="acceptance-backdrop" role="dialog" aria-modal="true" aria-label="Day 2 验收面板">
          <aside className="acceptance-panel glass-panel">
            <div className="acceptance-header">
              <div>
                <p className="panel-label">Acceptance Test</p>
                <h2>{activeTestPanel}</h2>
              </div>
              <button className="secondary-button" onClick={() => setActiveTestPanel(null)}>
                关闭
              </button>
            </div>

            {activeTestPanel === "runtime" ? (
            <section className="acceptance-section">
              <h3>1. 后端与任务状态</h3>
              <dl className="acceptance-kv">
                <div>
                  <dt>Backend</dt>
                  <dd>{backendStatus}</dd>
                </div>
                <div>
                  <dt>Job ID</dt>
                  <dd>{job?.job_id ?? "尚未运行审查"}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{job?.status ?? "not started"}</dd>
                </div>
                <div>
                  <dt>Document ID</dt>
                  <dd>{job?.document_id ?? "waiting for audit"}</dd>
                </div>
                <div>
                  <dt>Rejected</dt>
                  <dd>{job?.rejected_count ?? 0}</dd>
                </div>
              </dl>
            </section>
            ) : null}

            {activeTestPanel === "trace" ? (
            <section className="acceptance-section">
              <h3>ReviewTrace</h3>
              {job?.trace.steps.length ? (
                <ol className="trace-list">
                  {job.trace.steps.map((step) => (
                    <li className={`trace-item trace-${step.status}`} key={step.step_id}>
                      <div className="trace-item-header">
                        <strong>{step.name}</strong>
                        <span>{step.step_type} · {step.status}</span>
                      </div>
                      {step.input_summary ? <p>Input: {step.input_summary}</p> : null}
                      {step.output_summary ? <p>Output: {step.output_summary}</p> : null}
                      {step.error ? <p>Error: {step.error}</p> : null}
                      {step.metadata.tool_name ? <p>Tool: {String(step.metadata.tool_name)}</p> : null}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="muted-copy">还没有 trace。请选择文件并运行 Fake Audit。</p>
              )}
            </section>
            ) : null}

            {activeTestPanel === "candidates" ? (
            <section className="acceptance-section">
              <h3>Candidates / Rejected</h3>
              {job?.candidates.length ? (
                <div className="candidate-grid">
                  {job.candidates.map((candidate) => (
                    <article className="candidate-card" key={candidate.candidate_id}>
                      <div className="trace-item-header">
                        <strong>{candidate.title}</strong>
                        <span>{candidate.source_agent} · {Math.round(candidate.confidence * 100)}%</span>
                      </div>
                      <p>{candidate.description}</p>
                      <p>Candidate: {candidate.candidate_id}</p>
                      <p>Rule: {candidate.rule_id}</p>
                      <p>Evidence count: {candidate.evidences.length}</p>
                      {job.rejected_candidates.some(
                        (rejected) => rejected.candidate_id === candidate.candidate_id,
                      ) ? (
                        <p className="rejected-copy">
                          Rejected:{" "}
                          {job.rejected_candidates.find(
                            (rejected) => rejected.candidate_id === candidate.candidate_id,
                          )?.rejection_reason ?? "missing verified evidence"}
                        </p>
                      ) : null}
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">还没有 LLM mock candidate。请选择文件并运行 Fake Audit。</p>
              )}
            </section>
            ) : null}

            {activeTestPanel === "score" ? (
            <section className="acceptance-section">
              <h3>Score & Layer</h3>
              {job?.score ? (
                <div className="score-panel">
                  <div className="score-summary">
                    <strong>{job.score.total_score}</strong>
                    <span>{job.score.layer}</span>
                  </div>
                  <p>Template: {job.score.template_id}@{job.score.template_version}</p>
                  <p>Advantages: {job.score.advantage_tags.join(", ") || "none"}</p>
                  <div className="dimension-grid">
                    {Object.entries(job.score.dimension_scores).map(([name, value]) => (
                      <span key={name}>{name}: {value}</span>
                    ))}
                  </div>
                  <ul className="detail-list">
                    {job.score.calculation_details.map((detail) => (
                      <li key={detail}>{detail}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="muted-copy">还没有评分结果。</p>
              )}
            </section>
            ) : null}

            {activeTestPanel === "evidence" ? (
            <section className="acceptance-section">
              <h3>Evidence</h3>
              {findings.length ? (
                <div className="findings-list">
                  {findings.map((finding) => (
                    <article className="finding-card" key={`acceptance-${finding.finding_id}`}>
                      <strong>{finding.title}</strong>
                      {finding.evidences.map((evidence) => (
                        <p key={`${finding.finding_id}-${evidence.block_id}`}>
                          “{evidence.quote}” · page {evidence.page_number} · block {evidence.block_id} · {formatBBox(evidence.bbox)}
                        </p>
                      ))}
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted-copy">还没有正式 finding evidence。</p>
              )}
            </section>
            ) : null}

            {activeTestPanel === "openai" ? (
              <>
                <section className="acceptance-section">
                  <h3>OpenAI 官方接口设置</h3>
                  <div className="settings-form">
                    <label>
                      API Key
                      <input
                        type="password"
                        value={openAIKey}
                        placeholder="sk-..."
                        onChange={(event) => setOpenAIKey(event.target.value)}
                      />
                    </label>
                    <label>
                      Model
                      <input value={openAIModel} onChange={(event) => setOpenAIModel(event.target.value)} />
                    </label>
                    <label>
                      Base URL
                      <input value={openAIBaseUrl} onChange={(event) => setOpenAIBaseUrl(event.target.value)} />
                    </label>
                    <div className="audit-action-row">
                      <button className="primary-button" onClick={handleSaveOpenAISettings}>保存设置</button>
                      <button className="secondary-button" onClick={handleTestOpenAISettings}>测试设置</button>
                    </div>
                    <p className="muted-copy">
                      Status: {openAIStatus?.configured ? "configured" : "not configured"} · Model: {openAIStatus?.model ?? openAIModel}
                    </p>
                  </div>
                </section>
                <section className="acceptance-section">
                  <h3>从岗位 JD 创建模板</h3>
                  <div className="settings-form">
                    <label>
                      岗位名称
                      <input value={jobTemplateName} onChange={(event) => setJobTemplateName(event.target.value)} />
                    </label>
                    <label>
                      岗位 JD
                      <textarea value={jobTemplateJD} onChange={(event) => setJobTemplateJD(event.target.value)} />
                    </label>
                    <button className="primary-button" onClick={handleCreateJobTemplate}>调用 LLM 创建岗位模板</button>
                  </div>
                  {generatedTemplate ? (
                    <div className="score-panel">
                      <strong>{generatedTemplate.name}</strong>
                      <p>Template: {generatedTemplate.template_id}@{generatedTemplate.version}</p>
                      <p>Hard requirements: {generatedTemplate.hard_requirements.join(" / ")}</p>
                      <p>Advantages: {Object.values(generatedTemplate.advantage_dictionary).join(" / ")}</p>
                    </div>
                  ) : (
                    <p className="muted-copy">没有 API key 时不会 fallback 到规则解析，会明确返回错误。</p>
                  )}
                </section>
              </>
            ) : null}
          </aside>
        </div>
      ) : null}
    </main>
  );
}
