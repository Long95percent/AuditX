import pytest

from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.orchestrator import AgentOrchestrator
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.domain.resume_library import ReviewContext
from auditx.domain.scoring import JobTemplate
from auditx.tool_registry.base import Tool, ToolResult
from auditx.tool_registry.registry import ToolRegistry


def test_agent_orchestrator_records_accepted_and_rejected_candidates() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    orchestrator = AgentOrchestrator(extractor=FakeExtractor(include_invalid_finding=True))

    draft = orchestrator.review(document)

    assert len(draft.findings) == 1
    assert draft.findings[0].finding_id == "fake_valid_finding"
    assert draft.rejected_count == 1
    assert draft.trace.steps[0].step_type == "agent"
    assert draft.trace.steps[0].name == "fake_extractor.extract"
    assert any(step.status == "accepted" for step in draft.trace.steps)
    assert any(step.status == "rejected" for step in draft.trace.steps)


class FailingExtractor(FakeExtractor):
    def extract(self, document):
        raise RuntimeError("extractor unavailable")


def test_agent_orchestrator_isolates_extractor_failure() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    orchestrator = AgentOrchestrator(extractor=FailingExtractor())

    draft = orchestrator.review(document)

    assert draft.findings == []
    assert draft.rejected_count == 0
    assert draft.trace.steps[0].status == "failed"
    assert draft.trace.steps[0].error == "extractor unavailable"


def test_finding_candidate_allows_pending_without_evidence() -> None:
    from auditx.domain.review import FindingCandidate

    candidate = FindingCandidate(
        candidate_id="candidate_1",
        rule_id="llm.pending",
        title="待校验证据候选",
        description="Agent 可以先提出候选，但不能直接成为正式风险。",
        risk_level="medium",
        confidence=0.4,
        source_agent="llm_mock",
    )

    assert candidate.evidences == []


def test_agent_orchestrator_invokes_registered_extractor_tool() -> None:
    from auditx.agent_core.extractor_tool import ExtractorTool

    document = FakeDocumentParser().parse("demo_resume.pdf")
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FakeExtractor()))
    orchestrator = AgentOrchestrator(tool_registry=registry)

    draft = orchestrator.review(document)

    assert len(draft.findings) == 1
    assert draft.trace.steps[0].step_type == "tool"
    assert draft.trace.steps[0].name == "agent.extractor.fake"
    assert draft.trace.steps[0].metadata["tool_name"] == "agent.extractor.fake"


def test_agent_orchestrator_continues_when_registered_tool_fails() -> None:
    from auditx.agent_core.extractor_tool import ExtractorTool

    document = FakeDocumentParser().parse("demo_resume.pdf")
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FailingExtractor()))
    orchestrator = AgentOrchestrator(tool_registry=registry)

    draft = orchestrator.review(document)

    assert draft.findings == []
    assert draft.trace.steps[0].step_type == "tool"
    assert draft.trace.steps[0].status == "failed"
    assert draft.trace.steps[0].error == "extractor unavailable"


class ContextAssertingRuleTool(Tool):
    name = "resume.rule.context_asserting"
    description = "Test tool that requires orchestrator context."

    def run(self, input_data):
        assert isinstance(input_data["job_template"], JobTemplate)
        assert isinstance(input_data["context"], ReviewContext)
        assert input_data["context"].job_template.template_id == "frontend_engineer"
        return ToolResult(tool_name=self.name, ok=True, data={"candidates": []})


class ContextAssertingLLMTool(Tool):
    name = "agent.llm_mock.candidate_discovery"
    description = "Test LLM tool that requires orchestrator context."

    def run(self, input_data):
        assert isinstance(input_data["job_template"], JobTemplate)
        assert isinstance(input_data["context"], ReviewContext)
        return ToolResult(tool_name=self.name, ok=True, data={"candidates": [], "summary": "ok"})


def test_agent_orchestrator_passes_template_and_context_to_tools() -> None:
    from auditx.agent_core.extractor_tool import ExtractorTool

    document = FakeDocumentParser().parse("demo_resume.pdf")
    job_template = JobTemplate.sample_frontend()
    context = ReviewContext(job_template=job_template)
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FakeExtractor()))
    registry.register(ContextAssertingLLMTool())
    registry.register(ContextAssertingRuleTool())
    orchestrator = AgentOrchestrator(tool_registry=registry)

    draft = orchestrator.review(document=document, job_template=job_template, context=context)

    assert any(step.name == "agent.llm_mock.candidate_discovery" for step in draft.trace.steps)
    assert any(step.name == "resume.rule.context_asserting" for step in draft.trace.steps)
