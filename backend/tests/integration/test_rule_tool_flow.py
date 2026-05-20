from auditx.agent_core.extractor_tool import ExtractorTool
from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.llm_candidate_tool import LLMCandidateTool
from auditx.agent_core.orchestrator import AgentOrchestrator
from auditx.agent_core.rule_tools import ContactMissingRuleTool, FailingRuleTool
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.tool_registry.registry import ToolRegistry


def test_orchestrator_runs_rule_tools_and_records_trace_without_bypassing_agent() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FakeExtractor()))
    registry.register(LLMCandidateTool())
    registry.register(ContactMissingRuleTool())
    orchestrator = AgentOrchestrator(tool_registry=registry)

    draft = orchestrator.review(document)

    assert any(step.name == "resume.rule.contact_missing" for step in draft.trace.steps)
    rejected = next(
        candidate
        for candidate in draft.rejected_candidates
        if candidate.candidate_id == "rule_contact_missing"
    )
    assert rejected.source_agent == "resume.rule.contact_missing"
    assert rejected.rejection_reason == "missing verified evidence"
    assert all(finding.finding_id != "rule_contact_missing" for finding in draft.findings)


def test_rule_tool_failure_does_not_interrupt_orchestrator() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FakeExtractor()))
    registry.register(FailingRuleTool())
    orchestrator = AgentOrchestrator(tool_registry=registry)

    draft = orchestrator.review(document)

    assert len(draft.findings) == 1
    assert any(
        step.name == "resume.rule.failing" and step.status == "failed"
        for step in draft.trace.steps
    )
