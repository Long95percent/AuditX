import type { BBox, CandidateLayer } from "./audit";

export type ResumeStatus = "new" | "reviewed" | "shortlisted";
export type BatchStatus = "draft" | "running" | "completed" | "failed";
export type BatchCandidateStatus =
  | "pending"
  | "reviewing"
  | "reviewed"
  | "shortlisted"
  | "eliminated"
  | "failed";

export interface ResumeRecord {
  resume_id: string;
  filename: string;
  imported_at: string;
  status: ResumeStatus;
  parsed_document_id?: string | null;
}

export interface CandidateProfile {
  candidate_id: string;
  resume_id: string;
  display_name: string;
  source_file_path?: string | null;
  source_document_artifact_uri?: string | null;
  review_session_id?: string | null;
  summary?: string | null;
  skills: string[];
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CandidateScoreRecord {
  score_id: string;
  candidate_id: string;
  review_session_id: string;
  template_id: string;
  template_version: string;
  total_score: number;
  layer: CandidateLayer;
  dimension_scores: Record<string, number>;
  advantage_tags: string[];
  risk_count: number;
  batch_id?: string | null;
  created_at: string;
}

export interface CandidateFindingRecord {
  finding_id: string;
  candidate_id: string;
  review_session_id: string;
  title: string;
  risk_level: string;
  confidence: number;
  evidence_ids: string[];
  created_at: string;
}

export interface EvidenceIndexRecord {
  evidence_id: string;
  candidate_id: string;
  resume_id: string;
  parsed_document_artifact_uri: string;
  page_number: number;
  block_id: string;
  text_excerpt: string;
  bbox?: BBox | null;
  created_at: string;
}

export interface CandidateListItem {
  profile: CandidateProfile;
  latest_score?: CandidateScoreRecord | null;
}

export interface CandidateDetail {
  profile: CandidateProfile;
  scores: CandidateScoreRecord[];
  findings: CandidateFindingRecord[];
}

export interface BatchRecord {
  batch_id: string;
  name: string;
  status: BatchStatus;
  job_template_id: string;
  run_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface BatchCandidate {
  batch_id: string;
  candidate_id: string;
  status: BatchCandidateStatus;
  rank?: number | null;
  score_id?: string | null;
  included_reason?: string | null;
  eliminated_reason?: string | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}
