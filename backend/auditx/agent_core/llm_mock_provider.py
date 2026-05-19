from pydantic import BaseModel, Field

from auditx.domain.audit import RiskLevel
from auditx.domain.documents import ParsedDocument


class LLMMockCandidate(BaseModel):
    candidate_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: RiskLevel
    confidence: float = Field(ge=0, le=1)
    evidence_quote: str | None = None
    suggestion: str = ""


class LLMMockOutput(BaseModel):
    summary: str = Field(min_length=1)
    candidates: list[LLMMockCandidate] = Field(default_factory=list)


class LLMMockProvider:
    def analyze(self, document: ParsedDocument) -> LLMMockOutput:
        return LLMMockOutput(
            summary=f"LLM mock analyzed {document.document_id}",
            candidates=[
                LLMMockCandidate(
                    candidate_id="llm_candidate_company_a",
                    rule_id="llm.company.a_experience",
                    title="LLM 识别到 A 公司经历",
                    description="LLM mock 从简历文本中识别到候选人存在 A 公司任职经历。",
                    risk_level=RiskLevel.info,
                    confidence=0.72,
                    evidence_quote="任职于 A 公司",
                    suggestion="请结合岗位模板继续判断该经历是否构成优势或风险。",
                ),
                LLMMockCandidate(
                    candidate_id="llm_candidate_unverified_gap",
                    rule_id="llm.timeline.unverified_gap",
                    title="LLM 猜测存在未证实空档",
                    description="LLM mock 提出一个没有原文证据支撑的候选风险。",
                    risk_level=RiskLevel.medium,
                    confidence=0.38,
                    suggestion="没有证据时只能保留在 rejected/pending，不进入正式风险。",
                ),
            ],
        )
