from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class CandidateLayer(StrEnum):
    best = "best"
    potential = "potential"
    not_recommended = "not_recommended"


class JobTemplate(BaseModel):
    template_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    hard_requirements: list[str] = Field(default_factory=list)
    weights: dict[str, float]
    advantage_dictionary: dict[str, str] = Field(default_factory=dict)
    risk_strategy: dict[str, str] = Field(default_factory=dict)

    @field_validator("weights")
    @classmethod
    def weights_must_be_positive(cls, value: dict[str, float]) -> dict[str, float]:
        if any(weight < 0 for weight in value.values()):
            raise ValueError("weights must be non-negative")
        return value

    @classmethod
    def sample_frontend(cls) -> "JobTemplate":
        return cls(
            template_id="frontend_engineer",
            name="前端工程师",
            version="v1",
            hard_requirements=["具备前端项目经验", "熟悉 TypeScript"],
            weights={
                "completeness": 0.15,
                "hard_requirement_match": 0.2,
                "ability_match": 0.35,
                "experience_relevance": 0.2,
                "advantage_bonus": 0.1,
            },
            advantage_dictionary={
                "react": "React",
                "typescript": "TypeScript",
                "audit_trace": "审查链路意识",
            },
            risk_strategy={"missing_contact": "low", "timeline_gap": "medium"},
        )

    @classmethod
    def sample_finance(cls) -> "JobTemplate":
        return cls(
            template_id="finance_specialist",
            name="财务专员",
            version="v1",
            hard_requirements=["具备财务基础", "熟悉票据或成本流程"],
            weights={
                "completeness": 0.15,
                "hard_requirement_match": 0.3,
                "ability_match": 0.2,
                "experience_relevance": 0.25,
                "advantage_bonus": 0.1,
            },
            advantage_dictionary={
                "cost_control": "成本控制",
                "invoice": "票据处理",
                "audit_trace": "审计意识",
            },
            risk_strategy={"missing_contact": "low", "missing_education": "medium"},
        )

    @classmethod
    def sample_product_manager(cls) -> "JobTemplate":
        return cls(
            template_id="product_manager",
            name="产品经理",
            version="v1",
            hard_requirements=["具备需求分析经验", "能推动跨团队协作"],
            weights={
                "completeness": 0.1,
                "hard_requirement_match": 0.25,
                "ability_match": 0.25,
                "experience_relevance": 0.3,
                "advantage_bonus": 0.1,
            },
            advantage_dictionary={
                "roadmap": "路线图规划",
                "user_research": "用户研究",
                "audit_trace": "流程意识",
            },
            risk_strategy={"missing_contact": "low", "unclear_ownership": "medium"},
        )


class CandidateScoreInput(BaseModel):
    candidate_id: str = Field(min_length=1)
    completeness: float = Field(default=0, ge=0, le=1)
    hard_requirement_match: float = Field(default=0, ge=0, le=1)
    ability_match: float = Field(default=0, ge=0, le=1)
    experience_relevance: float = Field(default=0, ge=0, le=1)
    advantage_signals: list[str] = Field(default_factory=list)
    risk_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    precomputed_total_score: float | None = None
    precomputed_advantage_count: int | None = None

    @classmethod
    def scored_stub(
        cls,
        candidate_id: str,
        total_score: float,
        risk_count: int = 0,
        advantage_count: int = 0,
        created_at: datetime | None = None,
    ) -> "CandidateScoreInput":
        return cls(
            candidate_id=candidate_id,
            risk_count=risk_count,
            created_at=created_at or datetime.now(timezone.utc),
            precomputed_total_score=total_score,
            precomputed_advantage_count=advantage_count,
        )


class ScoreResult(BaseModel):
    candidate_id: str
    template_id: str
    template_version: str
    total_score: float
    layer: CandidateLayer
    dimension_scores: dict[str, int]
    advantage_tags: list[str] = Field(default_factory=list)
    calculation_details: list[str] = Field(default_factory=list)
    risk_count: int = 0
    created_at: datetime


class ScoringEngine:
    def score(self, score_input: CandidateScoreInput, template: JobTemplate) -> ScoreResult:
        dimension_scores = {
            "completeness": round(score_input.completeness * 100),
            "hard_requirement_match": round(score_input.hard_requirement_match * 100),
            "ability_match": round(score_input.ability_match * 100),
            "experience_relevance": round(score_input.experience_relevance * 100),
        }
        advantage_tags = [
            label
            for signal, label in template.advantage_dictionary.items()
            if signal in score_input.advantage_signals
        ]
        advantage_bonus = min(len(advantage_tags) * 10, 100)
        weighted_score = (
            dimension_scores["completeness"] * template.weights["completeness"]
            + dimension_scores["hard_requirement_match"] * template.weights["hard_requirement_match"]
            + dimension_scores["ability_match"] * template.weights["ability_match"]
            + dimension_scores["experience_relevance"] * template.weights["experience_relevance"]
            + advantage_bonus * template.weights["advantage_bonus"]
        )
        risk_penalty = min(score_input.risk_count * 5, 30)
        total_score = max(0, min(100, round(weighted_score - risk_penalty, 2)))
        details = [
            f"template={template.template_id}@{template.version}",
            f"advantage_bonus={advantage_bonus}",
            f"risk_penalty={risk_penalty}",
        ]
        if dimension_scores["hard_requirement_match"] < 60:
            details.append("hard_requirement_low_not_eliminated")
        return ScoreResult(
            candidate_id=score_input.candidate_id,
            template_id=template.template_id,
            template_version=template.version,
            total_score=total_score,
            layer=self._layer(total_score, dimension_scores),
            dimension_scores=dimension_scores,
            advantage_tags=advantage_tags,
            calculation_details=details,
            risk_count=score_input.risk_count,
            created_at=score_input.created_at,
        )

    def _layer(self, total_score: float, dimension_scores: dict[str, int]) -> CandidateLayer:
        if total_score >= 85 and dimension_scores["hard_requirement_match"] >= 60:
            return CandidateLayer.best
        if total_score >= 60:
            return CandidateLayer.potential
        return CandidateLayer.not_recommended


class TopNSelector:
    def __init__(self, default_n: int = 20) -> None:
        if default_n <= 0:
            raise ValueError("default_n must be greater than 0")
        self.default_n = default_n

    def select(self, candidates: list[CandidateScoreInput], n: int | None = None) -> list[CandidateScoreInput]:
        limit = self.default_n if n is None else n
        if limit <= 0:
            raise ValueError("n must be greater than 0")
        return sorted(candidates, key=self._sort_key)[:limit]

    def _sort_key(self, candidate: CandidateScoreInput) -> tuple[float, int, int, float]:
        total_score = candidate.precomputed_total_score or 0
        advantage_count = candidate.precomputed_advantage_count or len(candidate.advantage_signals)
        return (-total_score, candidate.risk_count, -advantage_count, -candidate.created_at.timestamp())
