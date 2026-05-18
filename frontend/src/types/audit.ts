export type RiskLevel = "high" | "medium" | "low" | "info";

export interface BBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface Evidence {
  document_id: string;
  page_number: number;
  block_id: string;
  quote: string;
  bbox: BBox;
  start_offset?: number | null;
  end_offset?: number | null;
}

export interface AuditFinding {
  finding_id: string;
  rule_id: string;
  title: string;
  description: string;
  risk_level: RiskLevel;
  confidence: number;
  evidences: Evidence[];
  suggestion: string;
  source_agent: string;
}

export type AuditJobStatus = "pending" | "running" | "completed" | "failed";

export interface AuditJob {
  job_id: string;
  file_path: string;
  status: AuditJobStatus;
  document_id?: string | null;
  findings: AuditFinding[];
  rejected_count: number;
  error?: string | null;
}
