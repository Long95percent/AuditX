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

export interface LayoutBlock {
  block_id: string;
  page_number: number;
  block_type: string;
  text: string;
  bbox: BBox;
}

export interface DocumentPage {
  page_number: number;
  width: number;
  height: number;
  blocks: LayoutBlock[];
}

export interface ParsedDocument {
  document_id: string;
  filename: string;
  pages: DocumentPage[];
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

export interface FindingCandidate {
  candidate_id: string;
  rule_id: string;
  title: string;
  description: string;
  risk_level: RiskLevel;
  confidence: number;
  evidences: Evidence[];
  suggestion: string;
  source_agent: string;
  rejection_reason?: string | null;
}

export interface ScoringSignal {
  signal_id: string;
  category: string;
  value: number | string | boolean;
  source_step: string;
  source_agent: string;
  reason: string;
}

export interface ArtifactRef {
  artifact_uri: string;
  artifact_type: string;
  content_type: string;
  sha256: string;
  size_bytes: number;
  created_at: string;
}

export type ReviewStepStatus = "started" | "accepted" | "rejected" | "failed";

export interface ReviewTraceStep {
  step_id: string;
  step_type: string;
  name: string;
  status: ReviewStepStatus;
  input_summary: string;
  output_summary: string;
  error?: string | null;
  metadata: Record<string, unknown>;
}

export interface ReviewTrace {
  steps: ReviewTraceStep[];
}

export type CandidateLayer = "best" | "potential" | "not_recommended";

export interface ScoreResult {
  candidate_id: string;
  template_id: string;
  template_version: string;
  total_score: number;
  layer: CandidateLayer;
  dimension_scores: Record<string, number>;
  advantage_tags: string[];
  calculation_details: string[];
  risk_count: number;
  created_at: string;
}

export interface JobTemplate {
  template_id: string;
  name: string;
  version: string;
  hard_requirements: string[];
  weights: Record<string, number>;
  advantage_dictionary: Record<string, string>;
  risk_strategy: Record<string, string>;
}

export type AuditJobStatus = "pending" | "running" | "completed" | "failed";

export interface AuditJob {
  job_id: string;
  file_path: string;
  status: AuditJobStatus;
  document_id?: string | null;
  findings: AuditFinding[];
  rejected_count: number;
  candidates: FindingCandidate[];
  rejected_candidates: FindingCandidate[];
  score?: ScoreResult | null;
  trace: ReviewTrace;
  artifacts: ArtifactRef[];
  error?: string | null;
}
