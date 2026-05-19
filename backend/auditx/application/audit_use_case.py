from auditx.agent_core.evidence_validator import EvidenceValidator
from auditx.agent_core.extractor import FindingExtractor
from auditx.agent_core.finding_normalizer import FindingNormalizer
from auditx.agent_core.orchestrator import AgentOrchestrator
from auditx.document_pipeline.base import DocumentParser
from auditx.domain.resume_library import ReviewContext
from auditx.domain.results import AuditResult
from auditx.domain.review import ReviewStepStatus, ReviewTraceStep
from auditx.domain.scoring import CandidateScoreInput, JobTemplate, ScoringEngine
from auditx.tool_registry.registry import ToolRegistry


class AuditUseCase:
    def __init__(
        self,
        parser: DocumentParser,
        extractor: FindingExtractor,
        normalizer: FindingNormalizer,
        evidence_validator: EvidenceValidator | None = None,
        tool_registry: ToolRegistry | None = None,
        job_template: JobTemplate | None = None,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        self.parser = parser
        self.extractor = extractor
        self.normalizer = normalizer
        self.evidence_validator = evidence_validator or EvidenceValidator()
        self.tool_registry = tool_registry
        self.job_template = job_template
        self.scoring_engine = scoring_engine or ScoringEngine()

    def run(self, file_path: str) -> AuditResult:
        document = self.parser.parse(file_path)
        context = ReviewContext(job_template=self.job_template) if self.job_template is not None else None
        draft = AgentOrchestrator(
            extractor=self.extractor,
            evidence_validator=self.evidence_validator,
            tool_registry=self.tool_registry,
        ).review(document=document, job_template=self.job_template, context=context)
        normalized_findings = self.normalizer.normalize(draft.findings)
        score = None
        if self.job_template is not None:
            score = self.scoring_engine.score(
                self._build_score_input(document.document_id, document.pages, normalized_findings, draft),
                self.job_template,
            )
            draft.trace.steps.append(
                ReviewTraceStep(
                    step_id="score_result",
                    step_type="tool",
                    name="scoring_engine.score",
                    status=ReviewStepStatus.accepted,
                    input_summary=document.document_id,
                    output_summary=f"Scored candidate {document.document_id} as {score.layer}",
                    metadata={
                        "template_id": score.template_id,
                        "template_version": score.template_version,
                        "total_score": score.total_score,
                        "layer": score.layer,
                        "risk_count": score.risk_count,
                    },
                )
            )
        return AuditResult(
            document=document,
            findings=normalized_findings,
            rejected_count=draft.rejected_count,
            candidates=draft.candidates,
            rejected_candidates=draft.rejected_candidates,
            score=score,
            trace=draft.trace,
        )

    def _build_score_input(self, document_id, pages, findings, draft) -> CandidateScoreInput:
        advantage_signals: list[str] = []
        matched_keywords: list[str] = []
        years_experience = 0
        for step in draft.trace.steps:
            advantage_signals.extend(step.metadata.get("advantage_signals", []))
            matched_keywords.extend(step.metadata.get("matched_keywords", []))
            years_experience = max(years_experience, step.metadata.get("years_experience", 0))

        unique_advantage_signals = sorted(set(advantage_signals))
        unique_matched_keywords = sorted(set(matched_keywords))
        risk_count = len([finding for finding in findings if finding.risk_level != "info"])
        candidate_count = len(draft.candidates)
        accepted_count = len(findings)
        return CandidateScoreInput(
            candidate_id=document_id,
            completeness=1.0 if pages else 0,
            hard_requirement_match=1.0 if unique_matched_keywords or accepted_count else 0.6,
            ability_match=min(1.0, (len(unique_advantage_signals) + len(unique_matched_keywords)) / 3),
            experience_relevance=min(1.0, max(years_experience / 3, accepted_count / 2)),
            advantage_signals=unique_advantage_signals,
            risk_count=risk_count + len(draft.rejected_candidates) + max(0, candidate_count - accepted_count),
        )
