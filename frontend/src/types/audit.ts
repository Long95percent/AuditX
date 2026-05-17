export type BBox = {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
};

export type Evidence = {
  documentId: string;
  pageNumber: number;
  blockId: string;
  quote: string;
  bbox: BBox;
};

export type RiskLevel = "high" | "medium" | "low" | "info";

export type AuditFinding = {
  findingId: string;
  ruleId: string;
  title: string;
  description: string;
  riskLevel: RiskLevel;
  confidence: number;
  evidences: Evidence[];
  suggestion: string;
  sourceAgent: string;
};
