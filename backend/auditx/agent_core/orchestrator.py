from auditx.agent_core.evidence_validator import EvidenceValidator
from auditx.agent_core.extractor import FindingExtractor
from auditx.domain.audit import AuditFinding
from auditx.domain.documents import ParsedDocument
from auditx.domain.resume_library import ReviewContext
from auditx.domain.review import (
    FindingCandidate,
    ReviewReportDraft,
    ReviewStepStatus,
    ReviewTrace,
    ReviewTraceStep,
)
from auditx.domain.scoring import JobTemplate
from auditx.tool_registry.registry import ToolRegistry


class AgentOrchestrator:
    def __init__(
        self,
        extractor: FindingExtractor | None = None,
        evidence_validator: EvidenceValidator | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.extractor = extractor
        self.evidence_validator = evidence_validator or EvidenceValidator()
        self.tool_registry = tool_registry

    def review(
        self,
        document: ParsedDocument,
        job_template: JobTemplate | None = None,
        context: ReviewContext | None = None,
    ) -> ReviewReportDraft:
        trace = ReviewTrace()
        candidate_findings = self._extract_candidates(document, trace, job_template, context)
        llm_candidates = self._discover_llm_candidates(document, trace, job_template, context)
        rule_candidates = self._run_rule_tools(document, trace, job_template, context)
        all_candidates = [*llm_candidates, *rule_candidates]
        accepted_findings: list[AuditFinding] = []
        rejected_candidates: list[FindingCandidate] = []
        rejected_count = 0

        for finding in candidate_findings:
            if self.evidence_validator.validate(finding, document):
                accepted_findings.append(finding)
                trace.steps.append(
                    self._step(
                        step_id=f"evidence_{finding.finding_id}",
                        name="evidence_validator.validate",
                        status=ReviewStepStatus.accepted,
                        output_summary=f"Accepted finding {finding.finding_id}",
                    )
                )
            else:
                rejected_count += 1
                trace.steps.append(
                    self._step(
                        step_id=f"evidence_{finding.finding_id}",
                        name="evidence_validator.validate",
                        status=ReviewStepStatus.rejected,
                        output_summary=f"Rejected finding {finding.finding_id}",
                    )
                )

        for candidate in all_candidates:
            finding = self._candidate_to_finding(candidate)
            if finding is not None and self.evidence_validator.validate(finding, document):
                accepted_findings.append(finding)
                trace.steps.append(
                    self._step(
                        step_id=f"candidate_{candidate.candidate_id}",
                        name="candidate_evidence_gate",
                        status=ReviewStepStatus.accepted,
                        output_summary=f"Accepted candidate {candidate.candidate_id}",
                        metadata={
                            "candidate_id": candidate.candidate_id,
                            "source_agent": candidate.source_agent,
                            "evidence_count": len(candidate.evidences),
                        },
                    )
                )
            else:
                rejection_reason = self._candidate_rejection_reason(candidate, finding)
                rejected_count += 1
                rejected_candidate = candidate.model_copy(
                    update={"rejection_reason": rejection_reason}
                )
                rejected_candidates.append(rejected_candidate)
                trace.steps.append(
                    self._step(
                        step_id=f"candidate_{candidate.candidate_id}",
                        name="candidate_evidence_gate",
                        status=ReviewStepStatus.rejected,
                        output_summary=f"Rejected candidate {candidate.candidate_id}: {rejection_reason}",
                        metadata={
                            "candidate_id": candidate.candidate_id,
                            "source_agent": candidate.source_agent,
                            "rejection_reason": rejection_reason,
                            "evidence_count": len(candidate.evidences),
                        },
                    )
                )

        return ReviewReportDraft(
            findings=accepted_findings,
            rejected_count=rejected_count,
            candidates=all_candidates,
            rejected_candidates=rejected_candidates,
            trace=trace,
        )

    def _extract_candidates(
        self,
        document: ParsedDocument,
        trace: ReviewTrace,
        job_template: JobTemplate | None,
        context: ReviewContext | None,
    ) -> list[AuditFinding]:
        if self.tool_registry is not None:
            return self._extract_candidates_with_tool(document, trace, job_template, context)
        if self.extractor is None:
            trace.steps.append(
                self._step(
                    step_id="agent_extract",
                    name="fake_extractor.extract",
                    status=ReviewStepStatus.failed,
                    input_summary=document.document_id,
                    error="No extractor or tool registry configured",
                )
            )
            return []
        try:
            findings = self.extractor.extract(document)
        except Exception as exc:
            trace.steps.append(
                self._step(
                    step_id="agent_extract",
                    name="fake_extractor.extract",
                    status=ReviewStepStatus.failed,
                    input_summary=document.document_id,
                    error=str(exc),
                )
            )
            return []

        trace.steps.append(
            self._step(
                step_id="agent_extract",
                name="fake_extractor.extract",
                status=ReviewStepStatus.accepted,
                input_summary=document.document_id,
                output_summary=f"Extracted {len(findings)} candidate findings",
            )
        )
        return findings

    def _discover_llm_candidates(
        self,
        document: ParsedDocument,
        trace: ReviewTrace,
        job_template: JobTemplate | None,
        context: ReviewContext | None,
    ) -> list[FindingCandidate]:
        if self.tool_registry is None or "agent.llm_mock.candidate_discovery" not in self.tool_registry.names():
            return []
        tool_name = "agent.llm_mock.candidate_discovery"
        try:
            result = self.tool_registry.get(tool_name).run(
                self._tool_input(document, job_template, context)
            )
        except Exception as exc:
            trace.steps.append(
                self._step(
                    step_id="llm_candidate_discovery",
                    name=tool_name,
                    status=ReviewStepStatus.failed,
                    input_summary=document.document_id,
                    error=str(exc),
                    metadata={"tool_name": tool_name},
                )
            )
            return []
        if not result.ok:
            trace.steps.append(
                self._step(
                    step_id="llm_candidate_discovery",
                    name=tool_name,
                    status=ReviewStepStatus.failed,
                    input_summary=document.document_id,
                    error=result.error,
                    metadata={"tool_name": result.tool_name},
                )
            )
            return []
        candidates = result.data.get("candidates", [])
        trace.steps.append(
            self._step(
                step_id="llm_candidate_discovery",
                name=tool_name,
                status=ReviewStepStatus.accepted,
                input_summary=document.document_id,
                output_summary=f"Discovered {len(candidates)} LLM candidates",
                metadata={
                    "tool_name": result.tool_name,
                    "candidate_count": len(candidates),
                    "summary": result.data.get("summary", ""),
                },
            )
        )
        return candidates

    def _run_rule_tools(
        self,
        document: ParsedDocument,
        trace: ReviewTrace,
        job_template: JobTemplate | None,
        context: ReviewContext | None,
    ) -> list[FindingCandidate]:
        if self.tool_registry is None:
            return []
        rule_tool_names = [
            name
            for name in self.tool_registry.names()
            if name.startswith(("resume.rule.", "resume.job."))
        ]
        candidates: list[FindingCandidate] = []
        for tool_name in rule_tool_names:
            try:
                result = self.tool_registry.get(tool_name).run(
                    self._tool_input(document, job_template, context)
                )
            except Exception as exc:
                trace.steps.append(
                    self._step(
                        step_id=f"rule_{tool_name}",
                        name=tool_name,
                        status=ReviewStepStatus.failed,
                        input_summary=document.document_id,
                        error=str(exc),
                        metadata={"tool_name": tool_name},
                    )
                )
                continue
            if not result.ok:
                trace.steps.append(
                    self._step(
                        step_id=f"rule_{tool_name}",
                        name=tool_name,
                        status=ReviewStepStatus.failed,
                        input_summary=document.document_id,
                        error=result.error,
                        metadata={"tool_name": result.tool_name},
                    )
                )
                continue
            tool_candidates = result.data.get("candidates", [])
            candidates.extend(tool_candidates)
            scoring_metadata = {
                key: value for key, value in result.data.items() if key != "candidates"
            }
            trace.steps.append(
                self._step(
                    step_id=f"rule_{tool_name}",
                    name=tool_name,
                    status=ReviewStepStatus.accepted,
                    input_summary=document.document_id,
                    output_summary=f"Resume tool produced {len(tool_candidates)} candidates",
                    metadata={
                        "tool_name": result.tool_name,
                        "candidate_count": len(tool_candidates),
                        **scoring_metadata,
                    },
                )
            )
        return candidates

    def _candidate_to_finding(self, candidate: FindingCandidate) -> AuditFinding | None:
        if not candidate.evidences:
            return None
        return AuditFinding(
            finding_id=candidate.candidate_id,
            rule_id=candidate.rule_id,
            title=candidate.title,
            description=candidate.description,
            risk_level=candidate.risk_level,
            confidence=candidate.confidence,
            evidences=candidate.evidences,
            suggestion=candidate.suggestion,
            source_agent=candidate.source_agent,
        )

    def _candidate_rejection_reason(
        self, candidate: FindingCandidate, finding: AuditFinding | None
    ) -> str:
        if not candidate.evidences or finding is None:
            return "missing verified evidence"
        return "invalid evidence reference"

    def _extract_candidates_with_tool(
        self,
        document: ParsedDocument,
        trace: ReviewTrace,
        job_template: JobTemplate | None,
        context: ReviewContext | None,
    ) -> list[AuditFinding]:
        tool_name = "agent.extractor.fake"
        try:
            result = self.tool_registry.get(tool_name).run(
                self._tool_input(document, job_template, context)
            )
        except Exception as exc:
            trace.steps.append(
                self._step(
                    step_id="tool_extract",
                    name=tool_name,
                    status=ReviewStepStatus.failed,
                    input_summary=document.document_id,
                    error=str(exc),
                    metadata={"tool_name": tool_name},
                )
            )
            return []

        if not result.ok:
            trace.steps.append(
                self._step(
                    step_id="tool_extract",
                    name=tool_name,
                    status=ReviewStepStatus.failed,
                    input_summary=document.document_id,
                    error=result.error,
                    metadata={"tool_name": result.tool_name},
                )
            )
            return []

        findings = result.data.get("findings", [])
        trace.steps.append(
            self._step(
                step_id="tool_extract",
                name=tool_name,
                status=ReviewStepStatus.accepted,
                input_summary=document.document_id,
                output_summary=f"Extracted {len(findings)} candidate findings",
                metadata={"tool_name": result.tool_name},
            )
        )
        return findings

    def _tool_input(
        self,
        document: ParsedDocument,
        job_template: JobTemplate | None,
        context: ReviewContext | None,
    ) -> dict[str, ParsedDocument | JobTemplate | ReviewContext | None]:
        return {"document": document, "job_template": job_template, "context": context}

    def _step(
        self,
        step_id: str,
        name: str,
        status: ReviewStepStatus,
        input_summary: str = "",
        output_summary: str = "",
        error: str | None = None,
        metadata: dict | None = None,
    ) -> ReviewTraceStep:
        return ReviewTraceStep(
            step_id=step_id,
            step_type="agent" if step_id == "agent_extract" else "tool",
            name=name,
            status=status,
            input_summary=input_summary,
            output_summary=output_summary,
            error=error,
            metadata=metadata or {},
        )
