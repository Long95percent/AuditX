import type { AuditFinding } from "../types/audit";

const sampleFindings: AuditFinding[] = [];

export function App() {
  return (
    <main className="app-shell">
      <section className="glass-panel hero-panel">
        <p className="eyebrow">AuditX / VeriDoc</p>
        <h1>Industrial Desktop Document Audit</h1>
        <p className="hero-copy">
          Evidence-first audit workspace for document preview, bbox-level findings,
          and Tauri sidecar orchestration.
        </p>
      </section>

      <section className="workspace-grid">
        <div className="glass-panel">Document Viewer Placeholder</div>
        <div className="glass-panel">Findings: {sampleFindings.length}</div>
        <div className="glass-panel timeline-panel">Audit Timeline Placeholder</div>
      </section>
    </main>
  );
}
